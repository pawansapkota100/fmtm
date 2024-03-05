import React, { useCallback, useState, useEffect } from 'react';

import CoreModules from '@/shared/CoreModules';
import { MapContainer as MapComponent } from '@/components/MapComponent/OpenLayersComponent';
import { useOLMap } from '@/components/MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '@/components/MapComponent/OpenLayersComponent/LayerSwitcher';
import { VectorLayer } from '@/components/MapComponent/OpenLayersComponent/Layers';
import { Vector as VectorSource } from 'ol/source';
import GeoJSON from 'ol/format/GeoJSON';
import { get } from 'ol/proj';
import environment from '@/environment';
import { getStyles } from '@/components/MapComponent/OpenLayersComponent/helpers/styleUtils';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { basicGeojsonTemplate } from '@/utilities/mapUtils';
import TaskSubmissionsMapLegend from '@/components/ProjectSubmissions/TaskSubmissionsMapLegend';
import Accordion from '@/components/common/Accordion';
import AsyncPopup from '@/components/MapComponent/OpenLayersComponent/AsyncPopup/AsyncPopup';
import {
  colorCodesType,
  federalWiseProjectCount,
  legendColorArrayType,
  taskBoundariesType,
  taskFeaturePropertyType,
  taskInfoType,
} from '@/models/task/taskModel';
import { isValidUrl } from '@/utilfunctions/urlChecker';
import { projectInfoType, projectTaskBoundriesType } from '@/models/project/projectModel';
import { useAppSelector } from '@/types/reduxTypes';

export const defaultStyles = {
  lineColor: '#000000',
  lineOpacity: 70,
  fillColor: '#1a2fa2',
  fillOpacity: 50,
  lineThickness: 1,
  circleRadius: 5,
  dashline: 0,
  showLabel: false,
  customLabelText: null,
  labelField: '',
  labelFont: 'Calibri',
  labelFontSize: 14,
  labelColor: '#000000',
  labelOpacity: 100,
  labelOutlineWidth: 3,
  labelOutlineColor: '#ffffff',
  labelOffsetX: 0,
  labelOffsetY: 0,
  labelText: 'normal',
  labelMaxResolution: 400,
  labelAlign: 'center',
  labelBaseline: 'middle',
  labelRotationDegree: 0,
  labelFontWeight: 'normal',
  labelPlacement: 'point',
  labelMaxAngleDegree: 45.0,
  labelOverflow: false,
  labelLineHeight: 1,
  visibleOnMap: true,
  icon: {},
  showSublayer: false,
  sublayerColumnName: '',
  sublayer: {},
};

export const municipalStyles = {
  ...defaultStyles,
  fillOpacity: 0,
  lineColor: '#008099',
  dashline: 5,
  width: 10,
};

const colorCodes: colorCodesType = {
  '#A9D2F3': { min: 10, max: 50 },
  '#7CB2E8': { min: 50, max: 100 },
  '#4A90D9': { min: 100, max: 130 },
  '#0062AC': { min: 130, max: 160 },
};
function colorRange(data, noOfRange) {
  if (data?.length === 0) return [];
  const actualCodes = [{ min: 0, max: 0, color: '#FF4538' }];
  const maxVal = Math.max(...data?.map((d) => d.count));
  const maxValue = maxVal <= noOfRange ? 10 : maxVal;
  // const minValue = Math.min(...data?.map((d) => d.count)) 0;
  const minValue = 1;
  // const firstValue = minValue;
  const colorCodesKeys = Object.keys(colorCodes);
  const interval = (maxValue - minValue) / noOfRange;
  let currentValue = minValue;
  colorCodesKeys.forEach((key, index) => {
    const nextValue = currentValue + interval;
    actualCodes.push({
      min: Math.round(currentValue),
      max: Math.round(nextValue),
      color: colorCodesKeys[index],
    });
    currentValue = nextValue;
  });
  return actualCodes;
}
const getChoroplethColor = (value, colorCodesOutput) => {
  let toReturn = '#FF4538';
  colorCodesOutput?.map((obj) => {
    if (obj.min <= value && obj.max >= value) {
      toReturn = obj.color;
      return toReturn;
    }
    return toReturn;
  });
  return toReturn;
};

const TaskSubmissionsMap = () => {
  const dispatch = CoreModules.useAppDispatch();
  const [taskBoundaries, setTaskBoundaries] = useState<taskBoundariesType | null>(null);
  const [dataExtractUrl, setDataExtractUrl] = useState<string | null>(null);
  const [dataExtractExtent, setDataExtractExtent] = useState(null);
  const projectInfo: projectInfoType = CoreModules.useAppSelector((state) => state.project.projectInfo);
  const projectTaskBoundries: projectTaskBoundriesType[] = CoreModules.useAppSelector(
    (state) => state.project.projectTaskBoundries,
  );

  const taskInfo = useAppSelector((state) => state.task.taskInfo);
  const federalWiseProjectCount: federalWiseProjectCount[] = taskInfo?.map((task) => ({
    code: task.task_id,
    count: task.submission_count,
  }));

  const selectedTask: number = CoreModules.useAppSelector((state) => state.task.selectedTask);
  const legendColorArray: legendColorArrayType[] = colorRange(federalWiseProjectCount, '4');
  const { mapRef, map } = useOLMap({
    center: [0, 0],
    zoom: 4,
    maxZoom: 25,
  });

  useEffect(() => {
    if (
      !projectTaskBoundries ||
      projectTaskBoundries?.length < 1 ||
      projectTaskBoundries?.[0]?.taskBoundries?.length < 1
    ) {
      return;
    }
    const taskGeojsonFeatureCollection = {
      ...basicGeojsonTemplate,
      features: [
        ...projectTaskBoundries?.[0]?.taskBoundries?.map((task) => ({
          ...task.outline_geojson,
          id: task.outline_geojson.properties.uid,
        })),
      ],
    };
    setTaskBoundaries(taskGeojsonFeatureCollection);
  }, [projectTaskBoundries]);

  useEffect(() => {
    if (!taskBoundaries) return;
    const filteredSelectedTaskGeojson = {
      ...basicGeojsonTemplate,
      features: taskBoundaries?.features?.filter((task) => task.properties.uid === selectedTask),
    };
    const vectorSource = new VectorSource({
      features: new GeoJSON().readFeatures(filteredSelectedTaskGeojson, {
        featureProjection: get('EPSG:3857'),
      }),
    });
    const extent = vectorSource.getExtent();

    setDataExtractExtent(vectorSource.getFeatures()[0].getGeometry());
    setDataExtractUrl(projectInfo.data_extract_url);

    map.getView().fit(extent, {
      // easing: elastic,
      animate: true,
      size: map?.getSize(),
      // maxZoom: 15,
      padding: [50, 50, 50, 50],
      // duration: 900,
      constrainResolution: true,
      duration: 2000,
    });
  }, [selectedTask]);

  const taskOnSelect = (properties, feature) => {
    dispatch(CoreModules.TaskActions.SetSelectedTask(properties.uid));
  };

  const setChoropleth = useCallback(
    (style, feature, resolution) => {
      const stylex = { ...style };
      stylex.fillOpacity = 80;
      const getFederal = federalWiseProjectCount?.find((d) => d.code == feature.getProperties().uid);
      const getFederalCount = getFederal?.count;
      stylex.labelMaxResolution = 1000;
      stylex.showLabel = true;
      // stylex.labelField = 'district_code';
      // stylex.customLabelText = getFederalName;
      const choroplethColor = getChoroplethColor(getFederalCount, legendColorArray);
      stylex.fillColor = choroplethColor;
      return getStyles({
        style: stylex,
        feature,
        resolution,
      });
    },
    [federalWiseProjectCount],
  );

  map?.on('loadstart', function () {
    map.getTargetElement().classList.add('spinner');
  });
  map?.on('loadend', function () {
    map.getTargetElement().classList.remove('spinner');
  });

  const taskSubmissionsPopupUI = (properties: taskFeaturePropertyType) => {
    const currentTask = taskInfo?.filter((task) => +task.task_id === properties.uid);
    if (currentTask?.length === 0) return;
    return (
      <div className="fmtm-h-fit">
        <h2 className="fmtm-border-b-[2px] fmtm-border-primaryRed fmtm-w-fit fmtm-pr-1">
          Task ID: #{currentTask?.[0]?.task_id}
        </h2>
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-1 fmtm-mt-1">
          <p>
            Expected Count: <span className="fmtm-text-primaryRed">{currentTask?.[0]?.feature_count}</span>
          </p>
          <p>
            Submission Count: <span className="fmtm-text-primaryRed">{currentTask?.[0]?.submission_count}</span>
          </p>
        </div>
      </div>
    );
  };

  return (
    <CoreModules.Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        gap: 2,
      }}
      className="fmtm-h-full"
    >
      <MapComponent
        ref={mapRef}
        mapInstance={map}
        className="map"
        style={{
          height: '100%',
          width: '100%',
        }}
      >
        <LayerSwitcherControl />
        {taskBoundaries && (
          <VectorLayer
            setStyle={(feature, resolution) =>
              setChoropleth({ ...municipalStyles, lineThickness: 3 }, feature, resolution)
            }
            geojson={taskBoundaries}
            mapOnClick={taskOnSelect}
            viewProperties={{
              size: map?.getSize(),
              padding: [50, 50, 50, 50],
              constrainResolution: true,
              duration: 2000,
            }}
            zoomToLayer
            zIndex={5}
          />
        )}
        <div className="fmtm-absolute fmtm-bottom-2 fmtm-left-2 sm:fmtm-bottom-5 sm:fmtm-left-5 fmtm-z-50 fmtm-rounded-lg">
          <Accordion
            body={<TaskSubmissionsMapLegend legendColorArray={legendColorArray} />}
            header={
              <p className="fmtm-text-lg fmtm-font-normal fmtm-my-auto fmtm-mb-[0.35rem] fmtm-ml-2">
                No. of Submissions
              </p>
            }
            onToggle={() => {}}
            className="fmtm-py-0 !fmtm-pb-0 fmtm-rounded-lg hover:fmtm-bg-gray-50"
            collapsed={true}
          />
        </div>
        {taskInfo?.length > 0 && <AsyncPopup map={map} popupUI={taskSubmissionsPopupUI} />}
        {dataExtractUrl && isValidUrl(dataExtractUrl) && (
          <VectorLayer fgbUrl={dataExtractUrl} fgbExtent={dataExtractExtent} zIndex={15} />
        )}
      </MapComponent>
    </CoreModules.Box>
  );
};

export default TaskSubmissionsMap;
