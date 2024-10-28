

# --- Define risk levels based on frequency ranges from the table ---
def classify_risk_frequency(frequency):
    """
    Classifies the risk based on the frequency of occurrence.
    
    Arg:
    frequency (float): Frequency value, typically between 0 and 100.
    
    Returns:
    float: A normalized score between 0 and 1 based on the risk classification.
    """
    if 99 < frequency <= 100:
        return  1
    elif 90 < frequency <= 99:
        return  0.84
    elif 66 < frequency <= 90:
        return  0.67
    elif 33 < frequency <= 66:
        return  0.5
    elif 10 <= frequency <= 33:
        return  0.34
    elif 1 <= frequency <= 10:
        return  0.17
    else:
        return  0
    

def classify_risk_score(score):
    """
    Classifies the risk based on the given score.
    
    Arg:
    score (float): Risk score between 0 and 1.
    
    Returns:
    tuple: A tuple containing the risk category (str) and the score (float).
    """
    if 0.84 < score <= 1:
        return "Virtually certain", score
    elif 0.67 < score <= 0.84:
        return "Very probable", score
    elif 0.5 < score <= 0.67:
        return "Probable", score
    elif 0.34 < score <= 0.5:
        return "As likely as not", score
    elif 0.17 < score <= 0.34:
        return "Unlikely", score
    elif 0 < score <= 0.17:
        return "Very unlikely", score
    else:
        return "Exceptionally improbable", score
    
    
def classify_score(score):
    """
    Classifies the suitability score.
    
    Arg:
    score (float): Suitability score between 0 and 1.
    
    Returns:
    tuple: A tuple containing the classification (str) and the associated color (str).
    """
    if score >= 0.75:
        return 'Very Suitable', 'cyan'
    elif 0.5 <= score < 0.75:
        return 'Suitable', 'green'
    elif 0.25 <= score < 0.5:
        return 'Marginally Suitable', 'orange'
    else:
        return 'Not Suitable', 'red'
    

def classify_score_exposure(score):
    """
    Classifies the exposure level based on the score.
    
    Arg:
    score (float): Exposure score between 0 and 1.
    
    Returns:
    tuple: A tuple containing the exposure level (str) and the associated color (str).
    """
    if score >= 0.75:
        return 'High Exposure', 'red'
    elif 0.5 <= score < 0.75:
        return 'Moderate Exposure', 'orange'
    elif 0.25 <= score < 0.5:
        return 'Low Exposure', 'green'
    else:
        return 'Minimal Exposure', 'cyan'