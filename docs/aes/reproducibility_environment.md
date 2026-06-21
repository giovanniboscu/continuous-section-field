**Requirements**

CSF requires Python 3.8 or newer.

The repository has been tested with Python 3.14.6.

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

```powershell
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field

python -m venv venv
.\venv\Scripts\activate
python --version

python -m pip install -e .
```
