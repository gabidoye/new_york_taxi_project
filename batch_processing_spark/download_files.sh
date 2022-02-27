
set -e

#from turtle import done


TAXI_TYPE=$1    #"yellow"
YEAR=$2    #2020

URL_PREFIX="https://s3.amazonaws.com/nyc-tlc/trip+data"

# for MONTH in {1..12}; do 
#     echo ${MONTH}
# done
for MONTH in {1..12}; do
  FMONTH=`printf "%02d" ${MONTH}`
  #echo ${FMONTH}
  URL="${URL_PREFIX}/${TAXI_TYPE}_tripdata_${YEAR}-${FMONTH}.csv"
  #echo ${URL}

  LOCAL_PREFIX="/Users/gabidoye/Documents/Data_Engineering_course/datasets/${TAXI_TYPE}/${YEAR}/${FMONTH}"
  LOCAL_FILE="${TAXI_TYPE}_tripdata_${YEAR}_${FMONTH}.csv"
  LOCAL_PATH="${LOCAL_PREFIX}/${LOCAL_FILE}"

  echo "donwloading ${URL} to ${LOCAL_PATH}"
  mkdir -p ${LOCAL_PREFIX}
  wget ${URL} -O ${LOCAL_PATH}

  echo "compressing ${LOCAL_PATH}"
  gzip ${LOCAL_PATH}
done