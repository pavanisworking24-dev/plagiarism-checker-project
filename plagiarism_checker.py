# SIMPLE version without NLTK
def check_plagiarism(new_text, existing_texts):
    """Simple plagiarism check without NLTK"""
    if not existing_texts:
        return 0.0
    
    best_score = 0.0
    new_words = set(new_text.lower().split())
    
    for existing in existing_texts:
        if not existing:
            continue
        
        existing_words = set(existing.lower().split())
        
        if not new_words or not existing_words:
            continue
        
        common = new_words.intersection(existing_words)
        score = len(common) / max(len(new_words), len(existing_words))
        score_percent = score * 100
        
        if score_percent > best_score:
            best_score = score_percent
    
    return best_score
