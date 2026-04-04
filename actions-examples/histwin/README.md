if you want to only try histwin then run 

**linux / Mac**
```
python3 -m venv venv
source venv/bin/activate
```
**Windows**
```
python3 -m venv venv
.\venv\Scripts\activate 
```
get the source from the repository  (not full clone)

```
git clone --filter=blob:none --no-checkout https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field
git sparse-checkout init --cone
git sparse-checkout set histwin
git checkout main
```
install and run 

on Linux 
```
pip install csfpy

chmod +x create_yaml-histwin.sh
./create_yaml-histwin.sh
```
on Windows
```
pip install csfpy

Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\create_yaml-histwin.sh
```
