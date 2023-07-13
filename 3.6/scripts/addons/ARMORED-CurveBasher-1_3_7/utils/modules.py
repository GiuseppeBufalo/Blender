# from .. utils import addon


def register_all_modules(folderstring, action='register', debug=False):
    # Only works for the immediate subfolder level.
    
    import os
    from .. utils import addon
    from importlib import import_module
    
    path = os.path.join(addon.get_path(), folderstring)
    files = [file[:-3] for file in os.listdir(path) if file.endswith('.py') and file != '__init__.py']

    if debug: print(f"From \'{folderstring}\' >>")

    for file in files:
        module = import_module('.'.join([addon.get_name(), folderstring, file]))
        method = getattr(module, action, None)
        
        if method:
            method()
            if debug: print(f'  Registered: {file}')
        else:
            print(f'  \'{action}()\' function not found in {file}')
                