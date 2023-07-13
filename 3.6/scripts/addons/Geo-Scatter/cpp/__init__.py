
# import os, platform, ctypes, re
# from .. resources.translate import translate

# # TODO support macOS and LinuxOS
# #   -> find ways how to compile ? 


# def get_compiled_fct(fct_name):
#     """get compiled cpp function"""

#     fct = None
#     cpp_folder = os.path.dirname(__file__)

#     # locate the compiled libs for user OS  & get function

#     if platform.system() == 'Windows':

#         dllpath = os.path.join(cpp_folder,"x64","Release","scatter.dll")
#         dll = ctypes.CDLL(dllpath)
#         fct = eval(f"dll.{fct_name}")

#     elif platform.system() == 'Linux':
#         print("TODO")

#     elif platform.system() == 'Darwin':
#         print("TODO")
    
#     if fct is None:
#         raise Exception(translate("Sorry your OS is not Supported by our compiled library? let us know what OS you are using."))
#     return fct



# # ooooooooo.                         o8o               .
# # `888   `Y88.                       `"'             .o8
# #  888   .d88'  .ooooo.   .oooooooo oooo   .oooo.o .o888oo  .ooooo.  oooo d8b
# #  888ooo88P'  d88' `88b 888' `88b  `888  d88(  "8   888   d88' `88b `888""8P
# #  888`88b.    888ooo888 888   888   888  `"Y88b.    888   888ooo888  888
# #  888  `88b.  888    .o `88bod8P'   888  o.  )88b   888 . 888    .o  888
# # o888o  o888o `Y8bod8P' `8oooooo.  o888o 8""888P'   "888" `Y8bod8P' d888b
# #                        d"     YD
# #                        "Y88888P'



# def register():
#     return 

# def unregister():
#     return 



# # if __name__ == "__main__":