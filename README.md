## StackIt: An AI-Enhanced Q&A Forum

### 1. Project Overview

**StackIt** is a sophisticated, full-stack Q&A forum platform designed for collaborative learning and structured knowledge sharing. Engineered with a clean, modern aesthetic and a focus on intuitive user experience, StackIt integrates a powerful AI assistant, "Stellar," to provide intelligent, context-aware answers alongside community contributions.

The platform is built to be robust, scalable, and feature-rich, providing a seamless environment for users to ask, answer, and discover information effectively.

### 2. Core Philosophy & Design

The system is architected around three core principles:

*   **User-Centric Design:** A polished, dark-theme-first interface with a responsive layout ensures a comfortable and engaging experience across all devices. The UI emphasizes clarity and ease of use, with custom-themed components and smooth transitions.
*   **Intelligent Assistance:** Beyond a simple forum, StackIt leverages the **Google Gemini 2.5 Flash API** to power its AI assistant, "Stellar." This provides users with instant, high-quality answers, augmenting the knowledge base created by the community.
*   **Scalable Architecture:** Built on a powerful Python and Flask backend with a PostgreSQL-ready database schema, the application is designed for performance and future growth.

### 3. System Architecture

#### **Backend Architecture**

*   **Framework:** Python with the Flask web framework, utilizing a modular structure for maintainability.
*   **Database:** SQLAlchemy ORM for robust data management, architected for PostgreSQL in production with a lightweight SQLite option for local development.
*   **Authentication:** Secure, session-based authentication using Flask-Login, featuring comprehensive role-based access control (RBAC) for `User`, `Admin`, and `AI` roles.
*   **AI Integration:** A dedicated service layer for the Google Gemini 2.5 Flash API, featuring resilient logic with retry mechanisms and graceful error handling.
*   **Semantic Search & Context:** A custom-built vectorization engine using **scikit-learn's TF-IDF** creates a semantic understanding of all forum content. This powers a highly relevant search and provides deep contextual data for the AI assistant.
*   **Form Handling:** Secure forms built with WTForms, including CSRF protection and server-side validation.

#### **Frontend Architecture**

*   **Templating & Structure:** Jinja2 for dynamic server-side rendering, paired with a responsive Bootstrap 5 grid system.
*   **Rich Text Editor:** The **Quill.js** rich text editor provides a powerful and intuitive interface for creating questions and answers, complete with custom-handled image uploads and user mention capabilities.
*   **Dynamic UI:** Vanilla JavaScript (ES6+) powers a suite of dynamic features, including:
    *   Asynchronous voting, editing, and reply submissions without page reloads.
    *   A real-time notification poller with a dynamic badge counter.
    *   A persistent dark mode toggle utilizing `localStorage`.
    *   Custom-themed confirmation dialogs that replace native browser alerts.
    *   An intelligent `@username` autocomplete dropdown with role indicators and keyboard navigation.
*   **Styling:** A custom, professionally designed CSS stylesheet works in harmony with the Bootstrap framework, complemented by Font Awesome for a rich icon set.

### 4. Key Features

#### **Content & Community**

*   **Q&A System:** Full CRUD functionality for questions and answers, governed by user ownership and permissions.
*   **Rich Content:** Users can format posts with bold, italics, lists, links, images, and more. AI-generated responses are automatically parsed from Markdown to styled HTML, including syntax-highlighted code blocks.
*   **Hierarchical Replies:** A nested reply system allows for threaded discussions on individual answers, with the Stellar AI automatically engaging when users reply to its answers.
*   **Voting & Acceptance:** Users can upvote and downvote answers, and question authors can mark one definitive answer as "Accepted," which is visually highlighted.
*   **Advanced Tagging:** A flexible, many-to-many tagging system allows for precise categorization and filtering of questions.

#### **AI & Intelligence**

*   **Stellar AI Assistant:** The Gemini-powered assistant can be invoked by mentioning `@Stellar` in a question, automatically generating a comprehensive answer.
*   **Contextual Awareness:** The AI leverages the TF-IDF vector database to understand the existing knowledge on the forum, allowing it to cite related discussions and avoid redundant answers.
*   **Dedicated AI Chat:** A full-page, persistent chat interface with Stellar AI allows users to have direct conversations, with the AI capable of referencing forum content.
*   **Semantic Search:** The search functionality goes beyond simple keywords, using vector similarity to find conceptually related questions and answers.

#### **User Experience & Management**

*   **Secure Authentication:** Users can register and log in via a secure system featuring robust password hashing.
*   **Dynamic Notifications:** A real-time notification system alerts users to new answers, replies, and `@username` mentions, with a dropdown for quick review.
*   **Profile & Reputation:** User profiles showcase activity history and a reputation score based on community engagement.
*   **Content Editing & Deletion:** Users can edit or delete their own contributions, with clear "(edited)" indicators and custom confirmation dialogs for destructive actions.
*   **Admin Panel:** A comprehensive dashboard provides administrators with full control over users, questions, and answers, including moderation tools and site analytics.

### 5. Technical Implementation Details

*   **Data Flow:** The application follows a standard MVC-like pattern, with user requests being handled by Flask routes, processed by business logic, interacting with the SQLAlchemy models, and rendered via Jinja2 templates. Asynchronous JavaScript calls to API endpoints handle all real-time UI updates.
*   **Scalability:** The architecture is designed for growth. The database can be seamlessly migrated from SQLite to PostgreSQL by changing a single environment variable. The use of SQLAlchemy's connection pooling and a stateless design philosophy ensures the application can be deployed behind a load balancer.
*   **Security:** Security is a core consideration, addressed through CSRF protection on all forms, strong password hashing with `passlib`, role-based authorization decorators, and validation of all user input.


### ⚠️ Developer Setup Notes

1. Create a `.env` file in the root directory of the project and add your Gemini API key:

    ```
    GEMINI_API_KEY="YOUR_API_KEY"
    ```

    Replace the empty string with your actual Gemini API key.

2. Install all required Python dependencies before running the app:

    ```bash
    pip install -r requirements.txt
    ```

3. Run the application with:

    ```bash
    python main.py
    ```

This ensures all backend services, including the AI integration with **Google Gemini 2.5 Flash**, work correctly.


