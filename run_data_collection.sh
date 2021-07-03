export path1="$(dirname "$0")"
cd $path1
echo "current working directory: "$PWD

DATE=`date +%m-%d-%Y`
source /home/malcolm/main/bin/activate

papermill S1_1_Run_Data_Collection.ipynb run_notebooks/S1_1_Run_Data_Collection_${DATE}.ipynb
export papermill_exit_status=$?

if [ $papermill_exit_status -eq 0 ]
then
  echo "removing " run_notebooks/S1_1_Run_Data_Collection_${DATE}.ipynb
  rm run_notebooks/S1_1_Run_Data_Collection_${DATE}.ipynb
  
fi


# 50 9 * * * * bash /home/malcolm/petfinder/run_data_collection.sh > /home/malcolm/Logs/petfinder_data_collection.log 2>&1