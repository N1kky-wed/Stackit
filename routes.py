import re
from flask import render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, desc, func
from datetime import datetime
from app import app, db
from models import User, Question, Answer, Tag, Vote, Notification, question_tags
from forms import LoginForm, RegisterForm, QuestionForm, AnswerForm, SearchForm
from ai_service import generate_ai_answer, check_stellar_mention
from vector_service import vector_db
import markdown
import json

@app.route('/')
def index():
    try:
        page = request.args.get('page', 1, type=int)
        search_query = request.args.get('search', '')
        tag_filter = request.args.get('tag', '')
        sort_by = request.args.get('sort', 'recent')
        
        query = Question.query
        
        # Apply search filter
        if search_query:
            query = query.filter(
                or_(Question.title.contains(search_query),
                    Question.description.contains(search_query))
            )
        
        # Apply tag filter
        if tag_filter:
            query = query.join(Question.tags).filter(Tag.name == tag_filter)
        
        # Apply sorting
        if sort_by == 'recent':
            query = query.order_by(desc(Question.created_at))
        elif sort_by == 'unanswered':
            query = query.filter(~Question.answers.any())
        
        questions = query.paginate(
            page=page, per_page=10, error_out=False
        )
        
        # Get popular tags with question count
        try:
            popular_tags = db.session.query(Tag, func.count(question_tags.c.question_id).label('question_count')) \
                                     .join(question_tags) \
                                     .group_by(Tag.id) \
                                     .order_by(desc('question_count')) \
                                     .limit(10).all()
        except Exception:
            # Fallback to simple tag query if join fails
            popular_tags = [(tag, 0) for tag in Tag.query.limit(10).all()]
        
        # Get community stats
        total_questions = Question.query.count()
        total_answers = Answer.query.count()
        total_users = User.query.count()
        
        return render_template('index.html',
                             questions=questions,
                             search_query=search_query,
                             tag_filter=tag_filter,
                             sort_by=sort_by,
                             popular_tags=popular_tags,
                             total_questions=total_questions,
                             total_answers=total_answers,
                             total_users=total_users)
    except Exception as e:
        app.logger.error(f"Error in index route: {e}")
        flash('An error occurred while loading questions. Please try again.', 'error')
        # Return empty results with safe defaults
        empty_pagination = type('obj', (object,), {
            'items': [], 'pages': 0, 'page': 1, 'has_prev': False, 'has_next': False,
            'prev_num': None, 'next_num': None, 'iter_pages': lambda: []
        })()
        return render_template('index.html',
                             questions=empty_pagination,
                             search_query=search_query or '',
                             tag_filter=tag_filter or '',
                             sort_by=sort_by or 'recent',
                             popular_tags=[],
                             total_questions=0,
                             total_answers=0,
                             total_users=0)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page or url_for('index'))
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'danger')
            return render_template('register.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'danger')
            return render_template('register.html', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/ask', methods=['GET', 'POST'])
@login_required
def ask_question():
    form = QuestionForm()
    if form.validate_on_submit():
        # Create question
        question = Question(
            title=form.title.data,
            description=form.description.data,
            user_id=current_user.id
        )
        
        # Process tags
        tag_names = [tag.strip() for tag in form.tags.data.split(',') if tag.strip()]
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            question.tags.append(tag)
        
        db.session.add(question)
        db.session.commit()
        
        # Update vector database
        vector_db.update_question(question.id)
        
        # Check for @Stellar mention - generate AI response in background
        if check_stellar_mention(form.description.data):
            from threading import Thread
            thread = Thread(target=generate_background_ai_response, 
                          args=(question.id, form.title.data, form.description.data, current_user.id))
            thread.daemon = True
            thread.start()
        
        flash('Your question has been posted!', 'success')
        return redirect(url_for('question_detail', id=question.id))
    
    return render_template('ask_question.html', form=form)

@app.route('/question/<int:id>')
def question_detail(id):
    question = Question.query.get_or_404(id)
    
    # Increment view count (only for non-authors to avoid inflating own views)
    if not current_user.is_authenticated or current_user.id != question.user_id:
        question.views += 1
        db.session.commit()
    
    # Get answers ordered by score and acceptance
    answers = Answer.query.filter_by(question_id=id).order_by(
        desc(Answer.is_accepted), desc(Answer.score)
    ).all()
    
    form = AnswerForm()
    
    return render_template('question_detail.html', 
                         question=question, 
                         answers=answers, 
                         form=form)

@app.route('/question/<int:id>/answer', methods=['POST'])
@login_required
def post_answer(id):
    question = Question.query.get_or_404(id)
    form = AnswerForm()
    
    if form.validate_on_submit():
        answer = Answer(
            content=form.content.data,
            question_id=id,
            user_id=current_user.id
        )
        db.session.add(answer)
        
        # Create notification for question author
        if question.user_id != current_user.id:
            notification = Notification(
                user_id=question.user_id,
                message=f"{current_user.username} answered your question: {question.title}",
                link=f"/question/{id}"
            )
            db.session.add(notification)
        
        db.session.commit()
        flash('Your answer has been posted!', 'success')
    
    return redirect(url_for('question_detail', id=id))

@app.route('/vote/<int:answer_id>/<vote_type>')
@login_required
def vote_answer(answer_id, vote_type):
    if vote_type not in ['up', 'down']:
        abort(400)
    
    answer = Answer.query.get_or_404(answer_id)
    existing_vote = Vote.query.filter_by(
        user_id=current_user.id, 
        answer_id=answer_id
    ).first()
    
    if existing_vote:
        if existing_vote.vote_type == vote_type:
            # Remove vote if clicking the same vote type
            db.session.delete(existing_vote)
        else:
            # Change vote type
            existing_vote.vote_type = vote_type
    else:
        # Create new vote
        vote = Vote(
            user_id=current_user.id,
            answer_id=answer_id,
            vote_type=vote_type
        )
        db.session.add(vote)
    
    # Update answer score
    upvotes = Vote.query.filter_by(answer_id=answer_id, vote_type='up').count()
    downvotes = Vote.query.filter_by(answer_id=answer_id, vote_type='down').count()
    answer.score = upvotes - downvotes
    
    db.session.commit()
    return redirect(url_for('question_detail', id=answer.question_id))

@app.route('/accept/<int:answer_id>')
@login_required
def accept_answer(answer_id):
    answer = Answer.query.get_or_404(answer_id)
    question = answer.question
    
    # Only question author can accept answers
    if question.user_id != current_user.id:
        abort(403)
    
    # Unaccept any previously accepted answer
    previous_accepted = Answer.query.filter_by(
        question_id=question.id, 
        is_accepted=True
    ).first()
    if previous_accepted:
        previous_accepted.is_accepted = False
    
    # Accept this answer
    answer.is_accepted = True
    
    # Create notification for answer author
    if answer.user_id != current_user.id:
        notification = Notification(
            user_id=answer.user_id,
            message=f"Your answer was accepted on: {question.title}",
            link=f"/question/{question.id}"
        )
        db.session.add(notification)
    
    db.session.commit()
    flash('Answer accepted!', 'success')
    return redirect(url_for('question_detail', id=question.id))



@app.route('/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(desc(Notification.created_at)).limit(20).all()
    
    # Mark all as read
    for notification in notifications:
        notification.is_read = True
    db.session.commit()
    
    return jsonify([{
        'id': n.id,
        'message': n.message,
        'link': n.link,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M')
    } for n in notifications])

@app.route('/notifications/count')
@login_required
def notification_count():
    count = Notification.query.filter_by(
        user_id=current_user.id, 
        is_read=False
    ).count()
    return jsonify({'count': count})

def generate_background_ai_response(question_id, title, description, user_id):
    """Generate AI response in background thread"""
    try:
        import threading
        import time
        import re
        
        def ai_response_task():
            with app.app_context():
                # Create AI user if it doesn't exist
                stellar_user = User.query.filter_by(username='Stellar').first()
                if not stellar_user:
                    stellar_user = User(
                        username='Stellar',
                        email='stellar@stackit.ai',
                        password_hash='no_login',
                        role='ai'
                    )
                    db.session.add(stellar_user)
                    db.session.commit()
                
                # Strip HTML tags for AI processing
                clean_description = re.sub(r'<[^>]+>', '', description)
                clean_title = re.sub(r'<[^>]+>', '', title)
                
                ai_answer_content = generate_ai_answer(clean_title, clean_description)
                # Convert markdown to HTML
                ai_answer_html = markdown.markdown(ai_answer_content, extensions=['codehilite', 'fenced_code'])
                
                ai_answer = Answer(
                    content=ai_answer_html,
                    question_id=question_id,
                    user_id=stellar_user.id
                )
                db.session.add(ai_answer)
                
                # Create notification for the user
                notification = Notification(
                    user_id=user_id,
                    message=f"Stellar answered your question!",
                    link=f"/question/{question_id}"
                )
                db.session.add(notification)
                db.session.commit()
        
        thread = threading.Thread(target=ai_response_task)
        thread.daemon = True
        thread.start()
        
    except Exception as e:
        app.logger.error(f"Error in background AI response: {e}")

@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    questions = Question.query.filter_by(user_id=user.id).order_by(desc(Question.created_at)).limit(10).all()
    answers = Answer.query.filter_by(user_id=user.id).order_by(desc(Answer.created_at)).limit(10).all()
    
    return render_template('profile.html', user=user, questions=questions, answers=answers)

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        abort(403)
    
    users = User.query.all()
    questions = Question.query.order_by(desc(Question.created_at)).limit(20).all()
    answers = Answer.query.order_by(desc(Answer.created_at)).limit(20).all()
    
    return render_template('admin.html', users=users, questions=questions, answers=answers)

@app.route('/delete_question/<int:id>', methods=['POST'])
@login_required
def delete_question(id):
    question = Question.query.get_or_404(id)
    
    # Only allow user to delete their own question or admin
    if current_user.id != question.user_id and current_user.role != 'admin':
        abort(403)
    
    db.session.delete(question)
    db.session.commit()
    
    # Update vector database
    vector_db.delete_question(id)
    
    flash('Question deleted successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/admin/delete_question/<int:id>')
@login_required
def admin_delete_question(id):
    if current_user.role != 'admin':
        abort(403)
    
    question = Question.query.get_or_404(id)
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted.', 'success')
    return redirect(url_for('admin'))

@app.route('/ai_chat_page')
@login_required
def ai_chat_page():
    """AI Chat page"""
    return render_template('ai_chat.html')

@app.route('/ai_chat', methods=['POST'])
@login_required
def ai_chat():
    """AI Chat endpoint with vector database context"""
    data = request.get_json()
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        # Get relevant context from vector database
        context = vector_db.get_context_for_chat(message, max_context=3)
        
        # Prepare context for AI
        context_text = ""
        if context:
            context_text = "\n\nRelevant forum discussions:\n"
            for item in context:
                context_text += f"- Question: {item['title']}\n  Description: {item['description']}\n"
                if item['answers']:
                    context_text += f"  Answers: {item['answers'][0][:100]}...\n"
                context_text += f"  Link: {item['link']}\n\n"
        
        # Generate AI response with context
        prompt = f"""You are Stellar, an AI assistant for the StackIt Q&A forum. 
User question: {message}

{context_text}

Please provide a helpful response. If you reference any of the forum discussions above, 
mention that you're referring to existing forum content. Be conversational and helpful."""
        
        ai_response = generate_ai_answer("Chat Question", prompt)
        
        return jsonify({
            'response': ai_response,
            'context': context
        })
        
    except Exception as e:
        return jsonify({
            'response': 'Sorry, I encountered an error while processing your request. Please try again.',
            'context': []
        })

@app.route('/rebuild_index')
@login_required
def rebuild_index():
    """Rebuild the vector database index (admin only)"""
    if current_user.role != 'admin':
        abort(403)
    
    success = vector_db.build_index()
    if success:
        flash('Vector database index rebuilt successfully!', 'success')
    else:
        flash('Failed to rebuild index.', 'error')
    
    return redirect(url_for('admin'))

@app.route('/admin/delete_answer/<int:id>')
@login_required
def admin_delete_answer(id):
    """Delete answer (admin only)"""
    if current_user.role != 'admin':
        abort(403)
    
    answer = Answer.query.get_or_404(id)
    question_id = answer.question_id
    db.session.delete(answer)
    db.session.commit()
    flash('Answer deleted successfully.', 'success')
    return redirect(url_for('admin'))

@app.route('/api/users')
@login_required
def api_users():
    """API endpoint for user mentions"""
    users = User.query.with_entities(User.username, User.role).all()
    return jsonify([{'username': u.username, 'role': u.role} for u in users])

@app.route('/edit_question/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_question(id):
    """Edit question (author or admin only)"""
    question = Question.query.get_or_404(id)
    
    if current_user.id != question.user_id and current_user.role != 'admin':
        abort(403)
    
    form = QuestionForm(obj=question)
    if form.validate_on_submit():
        question.title = form.title.data
        question.description = form.description.data
        question.is_edited = True
        question.updated_at = datetime.utcnow()
        
        # Update tags
        question.tags.clear()
        tag_names = [tag.strip() for tag in form.tags.data.split(',') if tag.strip()]
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, description=f"Questions about {tag_name}")
                db.session.add(tag)
            question.tags.append(tag)
        
        db.session.commit()
        vector_db.update_question(question.id)
        flash('Question updated successfully!', 'success')
        return redirect(url_for('question_detail', id=question.id))
    
    # Pre-populate tags
    if question.tags:
        form.tags.data = ', '.join([tag.name for tag in question.tags])
    
    return render_template('edit_question.html', form=form, question=question)

@app.route('/edit_answer/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_answer(id):
    """Edit answer (author or admin only)"""
    answer = Answer.query.get_or_404(id)
    
    if current_user.id != answer.user_id and current_user.role != 'admin':
        abort(403)
    
    form = AnswerForm(obj=answer)
    if form.validate_on_submit():
        answer.content = form.content.data
        answer.is_edited = True
        answer.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Answer updated successfully!', 'success')
        return redirect(url_for('question_detail', id=answer.question_id))
    
    return render_template('edit_answer.html', form=form, answer=answer)

@app.route('/reply_answer/<int:id>', methods=['POST'])
@login_required
def reply_answer(id):
    """Reply to an answer"""
    parent_answer = Answer.query.get_or_404(id)
    form = AnswerForm()
    
    if form.validate_on_submit():
        reply = Answer(
            content=form.content.data,
            question_id=parent_answer.question_id,
            user_id=current_user.id,
            parent_answer_id=parent_answer.id
        )
        db.session.add(reply)
        
        # Notify the original answer author
        if parent_answer.user_id != current_user.id:
            notification = Notification(
                user_id=parent_answer.user_id,
                message=f"{current_user.username} replied to your answer",
                link=url_for('question_detail', id=parent_answer.question_id)
            )
            db.session.add(notification)
        
        # If replying to Stellar, trigger AI response
        if parent_answer.author.username == 'Stellar':
            question = Question.query.get(parent_answer.question_id)
            generate_background_ai_response(
                question.id, 
                question.title, 
                form.content.data, 
                current_user.id
            )
        
        db.session.commit()
        flash('Reply posted successfully!', 'success')
    
    return redirect(url_for('question_detail', id=parent_answer.question_id))

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Advanced search page with filtering options"""
    form = SearchForm()
    questions = []
    total_results = 0
    
    # Get parameters from URL or form
    query = request.args.get('q', '') or (form.query.data if form.validate_on_submit() else '')
    tag_filter = request.args.get('tag', '')
    sort_by = request.args.get('sort', 'recent')  # recent, views, answers, unanswered
    date_filter = request.args.get('date', '')  # today, week, month
    page = request.args.get('page', 1, type=int)
    
    if query or tag_filter:
        # Build base query
        search_query = Question.query
        
        # Apply text search
        if query:
            search_query = search_query.filter(
                or_(Question.title.contains(query),
                    Question.description.contains(query))
            )
        
        # Apply tag filter
        if tag_filter:
            search_query = search_query.join(Question.tags).filter(Tag.name == tag_filter)
        
        # Apply date filter
        if date_filter:
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            if date_filter == 'today':
                search_query = search_query.filter(Question.created_at >= now - timedelta(days=1))
            elif date_filter == 'week':
                search_query = search_query.filter(Question.created_at >= now - timedelta(weeks=1))
            elif date_filter == 'month':
                search_query = search_query.filter(Question.created_at >= now - timedelta(days=30))
        
        # Apply sorting
        if sort_by == 'recent':
            search_query = search_query.order_by(desc(Question.created_at))
        elif sort_by == 'views':
            search_query = search_query.order_by(desc(Question.views))
        elif sort_by == 'answers':
            search_query = search_query.outerjoin(Answer).group_by(Question.id).order_by(desc(func.count(Answer.id)))
        elif sort_by == 'unanswered':
            search_query = search_query.filter(~Question.answers.any()).order_by(desc(Question.created_at))
        
        # Get total count
        total_results = search_query.count()
        
        # Paginate results
        questions = search_query.paginate(
            page=page, per_page=10, error_out=False
        )
    
    # Get all tags for filter dropdown
    all_tags = Tag.query.order_by(Tag.name).all()
    
    # Set form data if coming from URL parameters
    if query:
        form.query.data = query
    
    return render_template('search.html', 
                         form=form, 
                         questions=questions, 
                         total_results=total_results,
                         query=query,
                         tag_filter=tag_filter,
                         sort_by=sort_by,
                         date_filter=date_filter,
                         all_tags=all_tags)

@app.context_processor
def inject_template_vars():
    unread_count = 0
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    
    # Get popular tags with question count
    try:
        popular_tags = db.session.query(Tag, func.count(question_tags.c.question_id).label('question_count')) \
                                 .join(question_tags) \
                                 .group_by(Tag.id) \
                                 .order_by(desc('question_count')) \
                                 .limit(10).all()
    except Exception:
        # Fallback to simple tag query if join fails
        popular_tags = [(tag, 0) for tag in Tag.query.limit(10).all()]
    
    return {
        'unread_notification_count': unread_count,
        'popular_tags': popular_tags
    }
