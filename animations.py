def add_animation(result, confidence=0.0):
    """
    Returns appropriate animation based on the fake news detection result and confidence level.
    
    Args:
        result (str): 'Fake', 'Real', or 'Uncertain'
        confidence (float): Confidence score between 0.0 and 1.0
    
    Returns:
        dict: Animation details including class, icon, color scheme, and message
    """
    # Animation configurations with CSS classes, icons, and color schemes
    animations = {
        'fake': {
            'low': {
                'class': 'animation-fake-low',
                'icon': 'fa-exclamation-triangle',
                'color': 'amber',
                'message': 'Potentially misleading content detected with low confidence.'
            },
            'medium': {
                'class': 'animation-fake-medium',
                'icon': 'fa-exclamation-circle',
                'color': 'orange',
                'message': 'This content contains potentially false information.'
            },
            'high': {
                'class': 'animation-fake-high',
                'icon': 'fa-times-circle',
                'color': 'red',
                'message': 'High likelihood of false or misleading information!'
            }
        },
        'real': {
            'low': {
                'class': 'animation-real-low',
                'icon': 'fa-check',
                'color': 'light-green',
                'message': 'Appears to be factual, but verify with other sources.'
            },
            'medium': {
                'class': 'animation-real-medium',
                'icon': 'fa-check-circle',
                'color': 'green',
                'message': 'Content appears to be reliable.'
            },
            'high': {
                'class': 'animation-real-high',
                'icon': 'fa-shield-check',
                'color': 'teal',
                'message': 'High confidence in factual content.'
            }
        },
        'uncertain': {
            'default': {
                'class': 'animation-uncertain',
                'icon': 'fa-question-circle',
                'color': 'blue-grey',
                'message': 'Unable to determine reliability. Please verify from trusted sources.'
            }
        }
    }
    
    # Determine confidence level
    if confidence < 0.6:
        level = 'low'
    elif confidence < 0.85:
        level = 'medium'
    else:
        level = 'high'
    
    # Select animation based on result and confidence
    if result.lower() == 'fake':
        return animations['fake'][level]
    elif result.lower() == 'real':
        return animations['real'][level]
    else:
        # For uncertain or error cases
        return animations['uncertain']['default']