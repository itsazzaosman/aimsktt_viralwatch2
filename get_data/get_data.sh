mkdir -p ./insp_sitrep
mkdir -p ./worldpop
mkdir -p ./osrm
mkdir -p ./shapefiles

cp "C:/Users/STUDENT/OneDrive/Desktop/KTT Fellowship/aimsktt_viralwatch2/data/external/BDBV2026-Data/data/insp_sitrep/processed/"*.csv ./insp_sitrep/

cp "C:/Users/STUDENT/OneDrive/Desktop/KTT Fellowship/aimsktt_viralwatch2/data/external/BDBV2026-Data/data/worldpop/processed/"*.csv ./worldpop/

cp "C:/Users/STUDENT/OneDrive/Desktop/KTT Fellowship/aimsktt_viralwatch2/data/external/BDBV2026-Data/data/osrm/processed/"*.csv ./osrm/

cp -r "C:/Users/STUDENT/OneDrive/Desktop/KTT Fellowship/aimsktt_viralwatch2/data/external/BDBV2026-Data/data/shapefiles/"* ./shapefiles/