**Requirements**

CSF requires Python 3.8 or newer.

The repository has been tested with Python 3.14.6.

**Linux / macOS**


```bash
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field/

python3 -m venv venv
source venv/bin/activate
python --version

python -m pip install -e .
cd actions-examples/concrete_pole
mkdir {out/iso/,out/non-iso/}


```

**Windows**

```powershell
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field

py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python --version

python -m pip install -e .
cd actions-examples\concrete_pole
mkdir out\iso,
mkdir out\non-iso

```
