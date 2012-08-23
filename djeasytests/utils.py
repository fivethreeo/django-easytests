def settings_to_dict(settings):
    settings_dict = {}
    
    for key in settings.__dict__.keys():
        if not key.startswith('__'):
            setting = getattr(settings, key)
            if not callable(setting):
               settings_dict[key] = setting
               
    return settings_dict