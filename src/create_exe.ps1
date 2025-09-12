python -m PyInstaller --onefile `
--collect-all certifi `
--collect-all dnspython `
--collect-all inflect `
--collect-all typeguard `
--collect-all pymongo `
--add-data "$(python -m certifi);certifi" `
main.py
