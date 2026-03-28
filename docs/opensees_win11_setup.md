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

### 2. Clone the repository

```powershell
git clone https://github.com/giovanniboscu/continuous-section-field.git
```

### 3. Go to the project folder

```powershell
cd continuous-section-field
```

If you cloned the repository in a different location, use that path instead.

### 4. Create a new virtual environment with Python 3.12

```powershell
py -V:3.12 -m venv venv312
```

### 5. Verify that the Python executable from the new environment is the correct one

```powershell
.\venv312\Scripts\python.exe --version
.\venv312\Scripts\python.exe -c "import sys; print(sys.executable)"
```

---

## Install packages in the correct virtual environment

### 6. Upgrade `pip`

```powershell
.\venv312\Scripts\python.exe -m pip install --upgrade pip
```

### 7. Install `openseespy`

```powershell
.\venv312\Scripts\python.exe -m pip install openseespy
```

### 8. Install the local project and its dependencies

```powershell
.\venv312\Scripts\python.exe -m pip install -e .
```

This step installs the project in editable mode and should also install the dependencies declared by the project.

---

## Final verification

### 9. Verify that OpenSeesPy imports correctly

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
.\venv312\Scripts\python.exe example\csf_opensees_lab.py
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
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field
py -V:3.12 -m venv venv312
.\venv312\Scripts\python.exe -m pip install --upgrade pip
.\venv312\Scripts\python.exe -m pip install openseespy
.\venv312\Scripts\python.exe -m pip install -e .
.\venv312\Scripts\python.exe example\csf_opensees_check.py
```

---

## Practical note

This solution is stable **as long as**:

* you use `venv312`
* you run scripts with `.\venv312\Scripts\python.exe`
* you do not change the Python version
* you do not mix packages across different environments

It is not a universal guarantee for every future configuration.
