FROM ubuntu:jammy
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -yq install python3-pip
COPY simulator /simulator/
COPY src /src/
COPY data /data/
COPY model /model/
COPY requirements.txt /
# WORKDIR /simulator
RUN pip3 install -r requirements.txt
EXPOSE 8440
EXPOSE 8441
CMD ["python3", "src/hospital_system.py"]
#--messages=/data/messages.mllp --history=/data/history.csv --results=/data/results.csv --patients=/data/patients.csv
