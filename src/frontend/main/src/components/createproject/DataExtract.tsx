import React, { useEffect } from 'react';
import enviroment from '../../environment';
import CoreModules from '../../shared/CoreModules';
import FormGroup from '@mui/material/FormGroup';
import { FormCategoryService } from '../../api/CreateProjectService';
import { useNavigate, Link } from 'react-router-dom';
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
import { Divider, FormControl, Grid, InputLabel, MenuItem, Select, Typography } from '@mui/material';
import AssetModules from '../../shared/AssetModules.js';
import useForm from '../../hooks/useForm';
import SelectFormValidation from './validation/SelectFormValidation';
import DefineAreaMap from 'map/DefineAreaMap';
import DataExtractValidation from './validation/DataExtractValidation';

// import { SelectPicker } from 'rsuite';
let generateProjectLogIntervalCb = null;

const DataExtract: React.FC = ({ geojsonFile,setGeojsonFile,dataExtractFile,setDataExtractFile,setDataExtractFileValue }) => {
  const defaultTheme: any = CoreModules.useSelector<any>((state) => state.theme.hotTheme);
  const navigate = useNavigate();

  const dispatch = CoreModules.useDispatch();
  // //dispatch function to perform redux state mutation

  const formCategoryList = CoreModules.useSelector((state: any) => state.createproject.formCategoryList);
  // //we use use-selector from redux to get all state of formCategory from createProject slice

  const projectDetails = CoreModules.useSelector((state: any) => state.createproject.projectDetails);
  // //we use use-selector from redux to get all state of projectDetails from createProject slice

  // Fetching form category list
  useEffect(() => {
    dispatch(FormCategoryService(`${enviroment.baseApiUrl}/central/list-forms`));
  }, []);
  // END
  const selectExtractWaysList = ['Centroid', 'Polygon'];
  const selectExtractWays = selectExtractWaysList.map((item) => ({ label: item, value: item }));
  const formCategoryData = formCategoryList.map((item) => ({ label: item.title, value: item.title }));
  // //we use use-selector from redux to get state of dividedTaskGeojson from createProject slice
  const projectDetailsLoading = CoreModules.useSelector((state) => state.createproject.projectDetailsLoading);
  // //we use use-selector from redux to get state of dividedTaskGeojson from createProject slice

  // Fetching form category list
  useEffect(() => {
    dispatch(FormCategoryService(`${enviroment.baseApiUrl}/central/list-forms`));
  }, []);
  // END

  const submission = () => {
      // const previousValues = location.state.values;
      dispatch(CreateProjectActions.SetIndividualProjectDetailsData({ ...projectDetails, ...values }));
      navigate('/select-form');
    // navigate("/select-form", { replace: true, state: { values: values } });
  };

  // Fetching form category list
  useEffect(() => {
    dispatch(FormCategoryService(`${enviroment.baseApiUrl}/central/list-forms`));
    return () => {
      clearInterval(generateProjectLogIntervalCb);
      dispatch(CreateProjectActions.SetGenerateProjectLog(null));
    };
  }, []);
  // END

  const { handleSubmit, handleCustomChange, values, errors }: any = useForm(
    projectDetails,
    submission,
    DataExtractValidation,
  );
  
  return (
    <CoreModules.Stack
      sx={{
        width: { xs: '100%', md: '80%' },
        justifyContent: 'space-between',
        gap: '4rem',
        marginLeft: { md: '215px !important' },
        pr: 2,
      }}
    >
      <form onSubmit={handleSubmit}>
        <FormGroup>
          <Grid
            container
            spacing={{ xs: 2, md: 10 }}
            sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' } }}
          >
            <Grid item xs={16} md={4} sx={{ display: 'flex', flexDirection: 'column' }}>
            <CoreModules.FormControl sx={{ mb: 3 }}>
                <InputLabel
                  id="form-category"
                  sx={{
                    '&.Mui-focused': {
                      color: defaultTheme.palette.black,
                    },
                  }}
                >
                  Form Category
                </InputLabel>
                <Select
                  labelId="form_category-label"
                  id="form_category"
                  value={values.xform_title}
                  label="Form Category"
                  sx={{
                    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                      border: '2px solid black',
                    },
                  }}
                  onChange={(e) => {
                    handleCustomChange('xform_title', e.target.value);
                    dispatch(
                      CreateProjectActions.SetIndividualProjectDetailsData({
                        ...projectDetails,
                        xform_title: e.target.value,
                      }),
                    );
                  }}
                >
                  {/* onChange={(e) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'xform_title', value: e.target.value }))} > */}
                  {formCategoryData?.map((form) => (
                    <MenuItem value={form.value}>{form.label}</MenuItem>
                  ))}
                </Select>
                {errors.xform_title && (
                  <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
                    {errors.xform_title}
                  </CoreModules.FormLabel>
                )}
              </CoreModules.FormControl>
              <Divider sx={{m:2}}></Divider>
            
               {/* Area Geojson File Upload For Create Project */}
              <FormControl sx={{ mb: 3, width: '100%' }} variant="outlined">
                <CoreModules.FormLabel>Upload Custom Data Extract </CoreModules.FormLabel>
                <CoreModules.Button variant="contained" component="label">
                  <CoreModules.Input
                    sx={{color:'white'}}
                    type="file"
                    value={setDataExtractFileValue}
                    onChange={(e) => {
                      setDataExtractFile(e.target.files[0]);
                      handleCustomChange('data_extractFile', e.target.files[0]);
                    }}
                  />
                  <CoreModules.Typography component="h4">{dataExtractFile?.name}</CoreModules.Typography>
                </CoreModules.Button>
                {!dataExtractFile && (
                  <CoreModules.FormLabel component="h3" sx={{ mt: 2, color: defaultTheme.palette.error.main }}>
                    Geojson file is required.
                  </CoreModules.FormLabel>
                )}
              </FormControl>
              <Typography align='center' sx={{m:2}} component="h5">Or</Typography>
              
              
              <CoreModules.FormControl sx={{ mb: 3 }}>
                <InputLabel
                  id="form-category"
                  sx={{
                    '&.Mui-focused': {
                      color: defaultTheme.palette.black,
                    },
                  }}
                >
                  Select Data Extract Ways
                </InputLabel>
                <Select
                  labelId="data_extractWays-label"
                  id="data_extractWays"
                  value={values.data_extractWays}
                  label="Data Extract Category"
                  sx={{
                    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                      border: '2px solid black',
                    },
                  }}
                  onChange={(e) => {
                    handleCustomChange('data_extractWays', e.target.value);
                    dispatch(
                      CreateProjectActions.SetIndividualProjectDetailsData({
                        ...projectDetails,
                        data_extractWays: e.target.value,
                      }),
                    );
                  }}
                >
                  {/* onChange={(e) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'xform_title', value: e.target.value }))} > */}
                  {selectExtractWays?.map((form) => (
                    <MenuItem value={form.value}>{form.label}</MenuItem>
                  ))}
                </Select>
                {errors.data_extractWays && (
                  <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
                    {errors.data_extractWays}
                  </CoreModules.FormLabel>
                )}
              </CoreModules.FormControl> 
            </Grid>
          <Grid item md={8}>
            <CoreModules.Stack>
            <DefineAreaMap uploadedGeojson={geojsonFile} setGeojsonFile={setGeojsonFile} uploadedDataExtractFile={dataExtractFile}/>
            </CoreModules.Stack>
          </Grid>
          </Grid>
          <CoreModules.Stack
            sx={{
              display: 'flex',
              flexDirection: 'row',
              width: '100%',
              paddingRight: '5rem',
              gap: '12%',
            }}
          >
            {/* Previous Button  */}
            <Link to="/define-tasks">
              <CoreModules.Button sx={{ px: '20px' }} variant="outlined" color="error">
                Previous
              </CoreModules.Button>
            </Link>
            {/* END */}

            {/* Submit Button For Create Project on Area Upload */}
            <CoreModules.Stack sx={{ display: 'flex', justifyContent: 'flex-end' }}> 
            <CoreModules.LoadingButton
              // disabled={projectDetailsLoading}               
              type="submit"
              // loading={projectDetailsLoading}
              // loadingPosition="end"
              // endIcon={<AssetModules.SettingsSuggestIcon />}
              variant="contained"                            
              color="error"
              >
                Next
              </CoreModules.LoadingButton>
              
            </CoreModules.Stack>
            {/* END */}
          </CoreModules.Stack>
        </FormGroup>
      </form>
    </CoreModules.Stack>
  );
};
export default DataExtract;
