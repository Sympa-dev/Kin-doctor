def active_consultation(request):
    """
    Ajoute la consultation active au contexte de tous les templates
    """
    return {
        'active_consultation': getattr(request, 'active_consultation', None)
    }
