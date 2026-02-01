import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import string

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')

def preprocess_text(text):
    """Clean and prepare text for comparison"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    return text

def check_plagiarism(new_text, existing_texts):
    """Compare new text with existing texts"""
    # Prepare all texts
    all_texts = existing_texts + [new_text]
    processed_texts = [preprocess_text(t) for t in all_texts]
    
    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(processed_texts)
    
    # Calculate similarity
    similarity_matrix = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])
    
    # Get highest similarity score
    max_similarity = similarity_matrix.max()
    
    # Convert to percentage
    plagiarism_percent = max_similarity * 100
    
    return plagiarism_percent