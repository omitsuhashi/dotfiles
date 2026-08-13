# Commands required when fusionctl is invoked by non-interactive SSH.
typeset -U path PATH
path=(
  "$HOME/scripts"
  "/Applications/VMware Fusion.app/Contents/Public"
  $path
)
export PATH
