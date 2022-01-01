DATE=`date +%m-%d-%Y`
source /home/malcolm/main/bin/activate

papermill /home/malcolm/petfinder/S2_3_RunPetfinderEDA.ipynb /home/malcolm/petfinder/run_notebooks/S2_3_RunPetfinderEDA_${DATE}.ipynb
export papermill_exit_status=$?

if [ $papermill_exit_status -eq 0 ]
then
  echo "removing " /home/malcolm/petfinder/run_notebooks/S2_3_RunPetfinderEDA_${DATE}.ipynb
  rm /home/malcolm/petfinder/run_notebooks/S2_3_RunPetfinderEDA_${DATE}.ipynb
  
fi


# 50 9 * * * * bash /home/malcolm/petfinder/run_pf_eda.sh > /home/malcolm/Logs/pf_eda.log 2>&1