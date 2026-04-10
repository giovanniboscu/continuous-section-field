param(
    [Parameter(Mandatory=$true)]
    [string]$YAML
)

$SCRIPT = ".\csf_to_openfast.py"
$OUT    = "histwin_tower"

# -----------------------------------------------------------------------------
# GEOMETRY BLOCK
# -----------------------------------------------------------------------------
$E          = 210e9
$RHO        = 7850
$N_STATIONS = 11

# -----------------------------------------------------------------------------
# MACHINE / SIMULATION BLOCK
# -----------------------------------------------------------------------------
$RNA_MASS  = 350000
$RNA_IXX   = 4.0e7
$RNA_IYY   = 2.1e7
$RNA_IZZ   = 2.4e7
$RNA_CM_X  = 5.0
$RNA_CM_Z  = 2.0
$HUB_RAD   = 3.0
$OVERHANG  = 5.0

$TMAX = 10.0
$DT   = 0.01

# -----------------------------------------------------------------------------
# CALL
# -----------------------------------------------------------------------------
python $SCRIPT $YAML `
  --E $E `
  --rho $RHO `
  --n-stations $N_STATIONS `
  --rna-mass $RNA_MASS `
  --rna-ixx $RNA_IXX `
  --rna-iyy $RNA_IYY `
  --rna-izz $RNA_IZZ `
  --rna-cm-x $RNA_CM_X `
  --rna-cm-z $RNA_CM_Z `
  --hub-rad $HUB_RAD `
  --overhang $OVERHANG `
  --tmax $TMAX `
  --dt $DT `
  --out $OUT