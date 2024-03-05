import { CreateProjectStateTypes } from '@/store/types/ICreateProject';
import { createSlice } from '@reduxjs/toolkit';

export const initialState: CreateProjectStateTypes = {
  editProjectDetails: { name: '', description: '', short_description: '' },
  editProjectResponse: null,
  projectDetails: {
    dimension: 10,
    no_of_buildings: 5,
    hashtags: '',
    name: '',
    short_description: '',
    odk_central_url: '',
    odk_central_user: '',
    odk_central_password: '',
    description: '',
    organisation_id: null,
    per_task_instructions: '',
  },
  projectDetailsResponse: null,
  projectDetailsLoading: false,
  editProjectDetailsLoading: false,
  projectArea: null,
  projectAreaLoading: false,
  formCategoryList: [],
  formCategoryLoading: false,
  generateQrLoading: false,
  organisationList: [],
  organisationListLoading: false,
  generateQrSuccess: null,
  generateProjectLogLoading: false,
  generateProjectLog: null,
  createProjectStep: 1,
  dividedTaskLoading: false,
  dividedTaskGeojson: null,
  formUpdateLoading: false,
  taskSplittingGeojsonLoading: false,
  taskSplittingGeojson: null,
  updateBoundaryLoading: false,
  drawnGeojson: null,
  drawToggle: false,
  validateCustomFormLoading: false,
  validateCustomFormResponse: null,
  uploadAreaSelection: '',
  totalAreaSelection: null,
  splitTasksSelection: null,
  dataExtractGeojson: null,
  createProjectValidations: {},
  isUnsavedChanges: false,
  canSwitchCreateProjectSteps: false,
  isTasksGenerated: { divide_on_square: false, task_splitting_algorithm: false },
  isFgbFetching: false,
  toggleSplittedGeojsonEdit: false,
  customFileValidity: false,
};

const CreateProject = createSlice({
  name: 'createproject',
  initialState: initialState,
  reducers: {
    SetProjectDetails(state, action) {
      state.projectDetails = { ...state.projectDetails, [action.payload.key]: action.payload.value };
    },
    CreateProjectLoading(state, action) {
      state.projectDetailsLoading = action.payload;
    },
    PostProjectDetails(state, action) {
      state.projectDetailsResponse = action.payload;
    },
    ClearCreateProjectFormData(state) {
      // state.projectDetailsResponse = null
      state.projectDetails = {
        dimension: 10,
        no_of_buildings: 5,
        hashtags: '',
        name: '',
        short_description: '',
        odk_central_url: '',
        odk_central_user: '',
        odk_central_password: '',
        description: '',
        organisation_id: null,
      };
      state.projectArea = null;
      state.totalAreaSelection = null;
      state.splitTasksSelection = null;
      state.dataExtractGeojson = null;
      state.taskSplittingGeojson = null;
      state.drawnGeojson = null;
      state.generateProjectLog = null;
      state.generateProjectLogLoading = false;
      state.isUnsavedChanges = false;
      state.uploadAreaSelection = '';
      state.dividedTaskGeojson = null;
      state.dividedTaskLoading = false;
    },
    UploadAreaLoading(state, action) {
      state.projectAreaLoading = action.payload;
    },
    PostUploadAreaSuccess(state, action) {
      state.projectArea = action.payload;
    },
    GetFormCategoryLoading(state, action) {
      state.formCategoryLoading = action.payload;
    },
    GetFormCategoryList(state, action) {
      state.formCategoryList = action.payload;
    },
    SetIndividualProjectDetailsData(state, action) {
      state.projectDetails = action.payload;
    },
    GenerateProjectQRLoading(state, action) {
      state.generateQrLoading = action.payload;
    },
    GetOrganisationList(state, action) {
      state.organisationList = action.payload;
    },
    GetOrganisationListLoading(state, action) {
      state.organisationListLoading = action.payload;
    },
    GenerateProjectQRSuccess(state, action) {
      if (action.payload.status === 'SUCCESS') {
        state.generateQrSuccess = null;
      } else {
        state.generateQrSuccess = action.payload;
      }
    },
    SetGenerateProjectQRSuccess(state, action) {
      state.generateQrSuccess = action.payload;
    },
    GenerateProjectLogLoading(state, action) {
      state.generateProjectLogLoading = action.payload;
    },
    SetGenerateProjectLog(state, action) {
      state.generateProjectLog = action.payload;
    },
    SetCreateProjectFormStep(state, action) {
      state.createProjectStep = action.payload;
    },
    GetDividedTaskFromGeojsonLoading(state, action) {
      state.dividedTaskLoading = action.payload;
    },
    SetDividedTaskGeojson(state, action) {
      state.dividedTaskGeojson = action.payload;
    },
    SetDrawnGeojson(state, action) {
      state.drawnGeojson = action.payload;
    },
    SetDividedTaskFromGeojsonLoading(state, action) {
      state.dividedTaskLoading = action.payload;
    },
    //EDIT Project

    SetIndividualProjectDetails(state, action) {
      state.editProjectDetails = action.payload;
    },
    SetIndividualProjectDetailsLoading(state, action) {
      state.projectDetailsLoading = action.payload;
    },
    SetPatchProjectDetails(state, action) {
      state.editProjectResponse = action.payload;
    },
    SetPatchProjectDetailsLoading(state, action) {
      state.editProjectDetailsLoading = action.payload;
    },
    SetPostFormUpdateLoading(state, action) {
      state.formUpdateLoading = action.payload;
    },
    GetTaskSplittingPreviewLoading(state, action) {
      state.taskSplittingGeojsonLoading = action.payload;
    },
    GetTaskSplittingPreview(state, action) {
      state.dividedTaskGeojson = action.payload;
      // state.drawnGeojson = action.payload;
      state.taskSplittingGeojson = action.payload;
    },
    SetEditProjectBoundaryServiceLoading(state, action) {
      state.updateBoundaryLoading = action.payload;
    },
    SetDrawToggle(state, action) {
      state.drawToggle = action.payload;
    },
    ValidateCustomFormLoading(state, action) {
      state.validateCustomFormLoading = action.payload;
    },
    ValidateCustomForm(state, action) {
      state.validateCustomFormResponse = action.payload;
    },
    SetUploadAreaSelection(state, action) {
      state.uploadAreaSelection = action.payload;
    },
    SetTotalAreaSelection(state, action) {
      state.totalAreaSelection = action.payload;
    },
    SetSplitTasksSelection(state, action) {
      state.splitTasksSelection = action.payload;
    },
    setDataExtractGeojson(state, action) {
      state.dataExtractGeojson = action.payload;
    },
    SetCreateProjectValidations(state, action) {
      state.createProjectValidations = {
        ...state.createProjectValidations,
        [action.payload.key]: action.payload.value,
      };
    },
    SetIsUnsavedChanges(state, action) {
      state.isUnsavedChanges = action.payload;
    },
    SetCanSwitchCreateProjectSteps(state, action) {
      state.canSwitchCreateProjectSteps = action.payload;
    },
    SetIsTasksGenerated(state, action) {
      state.isTasksGenerated = {
        ...state.isTasksGenerated,
        [action.payload.key]: action.payload.value,
      };
    },
    SetFgbFetchingStatus(state, action) {
      state.isFgbFetching = action.payload;
    },
    ClearProjectStepState(state, action) {
      state.dividedTaskGeojson = null;
      state.splitTasksSelection = null;
      state.dataExtractGeojson = null;
      state.projectDetails = { ...action.payload, customLineUpload: null, customPolygonUpload: null };
    },
    SetToggleSplittedGeojsonEdit(state, action) {
      state.toggleSplittedGeojsonEdit = action.payload;
    },
    SetCustomFileValidity(state, action) {
      state.customFileValidity = action.payload;
    },
  },
});

export const CreateProjectActions = CreateProject.actions;
export default CreateProject.reducer;
