**Requirements**

CSF requires Python 3.8 or newer.

The repository has been tested with Python 3.14.6.

OpenSeesPy-dependent examples on Windows should be run with Python 3.12.

**Linux / macOS**

```bash
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field

python3 -m venv venv
source venv/bin/activate
python --version

python -m pip install -e .
```

**Linux / macOS with uv-managed Python**

```bash
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field

uv venv --python 3.14.6 venv
source venv/bin/activate
python --version

uv pip install -e .
```

**Windows**
For Windows/OpenSees setup instructions, see:

[OpenSees Win11 setup](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/opensees_win11_setup.md)

```powershell
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field

py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python --version

python -m pip install -e .
python -m pip install --no-cache-dir openseespy
```
