Write-Host "Path error regarding ...\src can be ignored."
cd src

python -m PyInstaller --onefile `
--collect-all certifi `
--collect-all dnspython `
--collect-all inflect `
--collect-all typeguard `
--collect-all pymongo `
--add-data "$(python -m certifi);certifi" `
main.py

cd ..

Write-Host "To run the exe, run .\src\dist\main.exe"
