import { task_split_type } from '@/types/enums';

export type CreateProjectStateTypes = {
  editProjectDetails: EditProjectDetailsTypes;
  editProjectResponse?: EditProjectResponseTypes | null;
  projectDetails: Partial<ProjectDetailsTypes>;
  projectDetailsResponse: EditProjectResponseTypes | null;
  projectDetailsLoading: boolean;
  editProjectDetailsLoading: boolean;
  projectArea: ProjectAreaTypes | null;
  projectAreaLoading: boolean;
  formCategoryList: FormCategoryListTypes[] | [];
  formCategoryLoading: boolean;
  generateQrLoading: boolean;
  organisationList: OrganisationListTypes[];
  organisationListLoading: boolean;
  generateQrSuccess: GenerateQrSuccessTypes | null;
  generateProjectLogLoading: boolean;
  generateProjectLog: GenerateProjectLogTypes | null;
  createProjectStep: number;
  dividedTaskLoading: boolean;
  dividedTaskGeojson: null | GeoJSONFeatureTypes;
  formUpdateLoading: boolean;
  taskSplittingGeojsonLoading: boolean;
  taskSplittingGeojson: TaskSplittingGeojsonTypes | null;
  updateBoundaryLoading: boolean;
  drawnGeojson: DrawnGeojsonTypes | null;
  drawToggle: boolean;
  validateCustomFormLoading: boolean;
  validateCustomFormResponse: ValidateCustomFormResponse | null;
  uploadAreaSelection: string;
  totalAreaSelection: string | null;
  splitTasksSelection: task_split_type | null;
  dataExtractGeojson: GeoJSONFeatureTypes | null;
  createProjectValidations: {};
  isUnsavedChanges: boolean;
  canSwitchCreateProjectSteps: boolean;
  isTasksGenerated: Record<string, any>;
  isFgbFetching: boolean;
  toggleSplittedGeojsonEdit: boolean;
  customFileValidity: boolean;
};
export type ValidateCustomFormResponse = {
  detail: { message: string; possible_reason: string };
};

export type GeometryTypes = {
  type: string;
  coordinates: number[][][];
};

export type GeoJSONFeatureTypes = {
  type: string;
  geometry: GeometryTypes;
  properties: Record<string, any>;
  id: string;
  bbox: null | number[];
  features?: [];
};

export type ProjectTaskTypes = {
  id: number;
  project_id: number;
  project_task_index: number;
  outline_geojson: GeoJSONFeatureTypes;
  outline_centroid: GeoJSONFeatureTypes;
  task_status: number;
  locked_by_uid: number | null;
  locked_by_username: string | null;
  task_history: any[];
  qr_code_base64: string;
  task_status_str: string;
};

export type ProjectInfoTypes = {
  name: string;
  short_description: string;
  description: string;
};

type EditProjectResponseTypes = {
  id: number;
  odkid: number;
  project_info: ProjectInfoTypes[];
  status: number;
  outline_geojson: GeoJSONFeatureTypes;
  tasks: ProjectTaskTypes[];
  xform_category: string;
  hashtags: string[];
};
export type EditProjectDetailsTypes = {
  name: string;
  description: string;
  short_description: string;
};

export type ProjectDetailsTypes = {
  dimension: number;
  data_extract_url?: string;
  task_split_dimension?: number;
  task_num_buildings?: number;
  no_of_buildings: number;
  odk_central_user?: string;
  odk_central_password?: string;
  organisation?: number;
  odk_central_url?: string;
  name?: string;
  hashtags?: string;
  short_description?: string;
  description?: string;
  task_split_type?: number;
  xform_category?: string;
  data_extract_options?: string;
  form_ways?: string;
  organisation_id?: number | null;
  formWays?: string;
  formCategorySelection?: string;
  average_buildings_per_task?: number;
  dataExtractWays?: string;
  per_task_instructions?: string;
};

export type ProjectAreaTypes = {
  // Define properties related to the project area here
};

export type FormCategoryListTypes = {
  id: number;
  title: string;
};

export type GenerateQrSuccessTypes = {
  Message: string;
  task_id: string;
};

export type OrganisationListTypes = {
  logo: string;
  id: number;
  url: string;
  slug: string;
  name: string;
  description: string;
  type: 1;
  odk_central_url: string | null;
};

export type GenerateProjectLogTypes = {
  status: string;
  message: string | null;
  progress: number;
  logs: string;
};

export type TaskSplittingGeojsonTypes = {
  // Define properties related to the task splitting GeoJSON here
};

export type DrawnGeojsonTypes = {
  type: string;
  properties: null;
  geometry: GeometryTypes;
  features?: [];
};
