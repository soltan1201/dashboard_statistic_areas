function processoExportarJSON(areaFeat, nameT){      
    var optExp = {
          'collection': ee.FeatureCollection(areaFeat), 
          'description': nameT, 
          'folder': 'SHP_in_geojson',      
          'fileFormat': 'GeoJSON'
        };    
    Export.table.toDrive(optExp) ;
    print(" salvando ... " + nameT + "..!")      ;
}



var param = {    
    "Assentamento_Brasil" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Assentamento_Brasil",
    "BR_ESTADOS_2022" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_ESTADOS_2022",
    "br_estados_raster": 'projects/mapbiomas-workspace/AUXILIAR/estados-2016-raster',
    "br_estados_shp": 'projects/mapbiomas-workspace/AUXILIAR/estados-2017',
    "BR_Municipios_2022" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_Municipios_2022",
    "BR_Pais_2022" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_Pais_2022",
    "Im_bioma_250" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Im_bioma_250",
    'vetor_biomas_250': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil',
    'biomas_250_rasters': 'projects/mapbiomas-workspace/AUXILIAR/RASTER/Bioma250mil',
    "Sigef_Brasil" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Sigef_Brasil",
    "Sistema_Costeiro_Marinho" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Sistema_Costeiro_Marinho",
    "aapd" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/aapd",
    "areas_Quilombolas" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/areas_Quilombolas",
    "buffer_pts_energias" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/buffer_pts_energias",
    "energias-dissolve-aneel" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/energias-dissolve-aneel",
    "florestaspublicas" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/florestaspublicas",
    "imovel_certificado_SNCI_br" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/imovel_certificado_SNCI_br",
    "macro_RH" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/macro_RH",
    "meso_RH" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/meso_RH",
    "micro_RH" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/micro_RH",
    "pnrh_asd" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/pnrh_asd",
    "prioridade-conservacao" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/prioridade-conservacao-caatinga-ibama",
    "prioridade-conservacao-V1" : "users/solkancengine17/shps_public/prioridade-conservacao-semiarido_V1",
    "prioridade-conservacao-V2" : "users/solkancengine17/shps_public/prioridade-conservacao-semiarido_V2",
    "tis_poligonais_portarias" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/tis_poligonais_portarias",
    "transposicao-cbhsf" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/transposicao-cbhsf",
    "nucleos_desertificacao" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/pnrh_nucleos_desertificacao",
    "UnidadesConservacao_S" : "projects/mapbiomas-workspace/AUXILIAR/areas-protegidas",
    "unidade_gerenc_RH_SNIRH_2020" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/unidade_gerenc_RH_SNIRH_2020",
    "reserva_biosfera" : "projects/mapbiomas-workspace/AUXILIAR/RESERVA_BIOSFERA/caatinga-central-2019",
    "semiarido2024": 'projects/mapbiomas-workspace/AUXILIAR/SemiArido_2024',
    'semiarido' : 'users/mapbiomascaatinga04/semiarido_rec',
    "irrigacao": 'projects/ee-mapbiomascaatinga04/assets/polos_irrigaaco_atlas',
    "energiasE": 'projects/ee-mapbiomascaatinga04/assets/energias_renovaveis',
    "bacia_sao_francisco" : 'users/solkancengine17/shps_public/bacia_sao_francisco',
    "matopiba": 'projects/mapbiomas-fogo/assets/territories/matopiba'
}

var lst_nameAsset = [
    "br_estados_shp",
    "vetor_biomas_250",
    "semiarido2024",
    'Assentamento_Brasil', 
    "nucleos_desertificacao",
    "UnidadesConservacao_S", 
    'areas_Quilombolas', 
    "macro_RH", "meso_RH", 
    'micro_RH', 
    'prioridade-conservacao-V1', 
    'prioridade-conservacao-V2', 
    'tis_poligonais_portarias', 
    "reserva_biosfera",
    'matopiba',
    "energiasE",    
    "bacia_sao_francisco",
];                          

lst_nameAsset.forEach(
    function(key_dict){
        var feat_tmp = ee.FeatureCollection(param[key_dict]);
        print(key_dict, feat_tmp.limit(10));
        processoExportarJSON(feat_tmp, key_dict);
        Map.addLayer(feat_tmp, {}, key_dict, false);
    }
)