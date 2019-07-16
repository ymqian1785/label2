import os

class DefaultPath:
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    software_name = 'autoLabel'

    testImgPath = os.path.normpath(os.path.join(root_path, 'tests\\photo\\1533882060.522232.jpg'))
    testImgsPath = os.path.normpath(os.path.join(root_path, 'tests\\photo\\*1533882060.522232.jpg'))

    # file path
    defaultFileDBPath = os.path.normpath(os.path.join(root_path, 'photo_path.tmp'))

    # upgrade.bat
    upgradePath = os.path.join(os.path.dirname(root_path),'upgrade.bat')

    # lasso path
    lassoDllPath = os.path.normpath(os.path.join(root_path, 'custom_dll\\lasso_dll\\Lasso.dll'))
    # lassoDllPath = os.path.normpath(os.path.join(root_path, 'Lasso.dll'))

    # FTP
    host_ip = "221.224.17.27"
    host_port = 10000
    username='ftp'
    password='123456qwerty'
    bufsize = 1024*1024

    ftpSoftwarePath='autoLabel_software'
    ftpDataPath='labeled_data'
    ftpResultPath='labeled_result'
