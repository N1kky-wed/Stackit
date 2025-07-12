import json
import re
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from models import Question, Answer
from app import db

class VectorDatabase:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.question_vectors = None
        self.question_data = []
        self.data_file = 'vector_data.pkl'
        
    def clean_html(self, text):
        """Remove HTML tags from text"""
        return re.sub(r'<[^>]+>', '', text)
    
    def preprocess_text(self, text):
        """Clean and preprocess text for vectorization"""
        text = self.clean_html(text)
        text = re.sub(r'[^\w\s]', ' ', text)
        return text.lower().strip()
    
    def build_index(self):
        """Build or rebuild the vector index from all questions and answers"""
        questions = Question.query.all()
        
        # Prepare data for vectorization
        documents = []
        question_data = []
        
        for question in questions:
            # Combine question title and description
            question_text = f"{question.title} {question.description}"
            processed_text = self.preprocess_text(question_text)
            
            # Get all answers for this question
            answers = Answer.query.filter_by(question_id=question.id).all()
            answer_texts = []
            for answer in answers:
                clean_answer = self.clean_html(answer.content)
                answer_texts.append(clean_answer)
            
            # Store question data
            question_info = {
                'id': question.id,
                'title': question.title,
                'description': self.clean_html(question.description),
                'author': question.author.username,
                'created_at': question.created_at.isoformat(),
                'tags': [tag.name for tag in question.tags],
                'answers': answer_texts,
                'answer_count': len(answer_texts),
                'views': question.views
            }
            
            question_data.append(question_info)
            documents.append(processed_text)
        
        if documents:
            # Create vectors
            self.question_vectors = self.vectorizer.fit_transform(documents)
            self.question_data = question_data
            
            # Save to file
            self.save_index()
            
            return True
        return False
    
    def save_index(self):
        """Save the vector index to disk"""
        data = {
            'vectorizer': self.vectorizer,
            'question_vectors': self.question_vectors,
            'question_data': self.question_data
        }
        with open(self.data_file, 'wb') as f:
            pickle.dump(data, f)
    
    def load_index(self):
        """Load the vector index from disk"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'rb') as f:
                    data = pickle.load(f)
                self.vectorizer = data['vectorizer']
                self.question_vectors = data['question_vectors']
                self.question_data = data['question_data']
                return True
            except:
                return False
        return False
    
    def search_similar(self, query, top_k=5):
        """Search for similar questions using vector similarity"""
        if self.question_vectors is None:
            if not self.load_index():
                if not self.build_index():
                    return []
        
        # Process query
        processed_query = self.preprocess_text(query)
        query_vector = self.vectorizer.transform([processed_query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.question_vectors)[0]
        
        # Get top results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Minimum similarity threshold
                result = self.question_data[idx].copy()
                result['similarity'] = float(similarities[idx])
                results.append(result)
        
        return results
    
    def get_context_for_chat(self, query, max_context=3):
        """Get relevant context for AI chat"""
        similar_questions = self.search_similar(query, top_k=max_context)
        
        context = []
        for q in similar_questions:
            context_item = {
                'question_id': q['id'],
                'title': q['title'],
                'description': q['description'][:200] + '...' if len(q['description']) > 200 else q['description'],
                'answers': q['answers'][:2],  # Include top 2 answers
                'link': f"/question/{q['id']}",
                'similarity': q['similarity']
            }
            context.append(context_item)
        
        return context
    
    def update_question(self, question_id):
        """Update a single question in the index"""
        # For simplicity, rebuild the entire index
        # In production, you'd want incremental updates
        self.build_index()
    
    def delete_question(self, question_id):
        """Remove a question from the index"""
        # For simplicity, rebuild the entire index
        # In production, you'd want incremental updates
        self.build_index()

# Global instance
vector_db = VectorDatabase()