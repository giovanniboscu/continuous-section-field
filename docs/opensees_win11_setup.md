# OpenSeesPy on Win11 with a Python 3.12 virtual environment

## Observed problem

`openseespy` appeared to be installed, but the script failed with an error like:

```text
RuntimeError: openseespy not available. Install openseespy.
```

The real cause was that the environment was using **Python 3.14**, while in the verified Windows setup `OpenSeesPy` worked correctly with **Python 3.12**.

---

## Full procedure

### 1. Install Python 3.12 if it is missing

```powershell
py install 3.12
```

### 2. Go to the project folder

```powershell
cd C:\Users\Gio\test_csf\continuous-section-field
```

### 3. Create a new virtual environment with Python 3.12

```powershell
py -V:3.12 -m venv venv312
```

### 4. Verify that the Python executable from the new environment is the correct one

```powershell
.\venv312\Scripts\python.exe --version
.\venv312\Scripts\python.exe -c "import sys; print(sys.executable)"
```

Expected output similar to:

```text
Python 3.12.10
C:\Users\Gio\test_csf\continuous-section-field\venv312\Scripts\python.exe
```

---

## Install packages in the correct virtual environment

### 5. Upgrade `pip`

```powershell
.\venv312\Scripts\python.exe -m pip install --upgrade pip
```

### 6. Install `openseespy`

```powershell
.\venv312\Scripts\python.exe -m pip install openseespy
```

### 7. Install the local project and its dependencies

```powershell
.\venv312\Scripts\python.exe -m pip install -e .
```
---

## Final verification

### 8. Verify that OpenSeesPy imports correctly

```powershell
.\venv312\Scripts\python.exe -c "import openseespy.opensees as ops; print(ops.version())"
```

Expected output:

```text
3.8.0
```

---

## Run the script

### 10. Run the script explicitly using the Python executable from the new virtual environment

```powershell
.\venv312\Scripts\python.exe example\csf_opensees_check.py
```

This is the most important point: **do not use a generic `python` command**, because it may point to a different installation, for example Python 3.14.

---

## Recommended future usage

To avoid confusion, always run commands in this form:

```powershell
.\venv312\Scripts\python.exe your_script.py
```

Or, for a quick check:

```powershell
.\venv312\Scripts\python.exe -c "import openseespy.opensees as ops; print(ops.version())"
```

---

## Essential summary

```powershell
cd C:\Users\Gio\test_csf\continuous-section-field
py -V:3.12 -m venv venv312
.\venv312\Scripts\python.exe -m pip install --upgrade pip
```
