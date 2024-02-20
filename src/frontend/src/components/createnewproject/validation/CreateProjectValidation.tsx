import { isValidUrl } from '@/utilfunctions/urlChecker';

interface ProjectValues {
  organisation_id: string;
  name: string;
  username: string;
  id: string;
  short_description: string;
  description: string;
  hashtags: string;
  odk_central_url: string;
  odk_central_user: string;
  odk_central_password: string;
  defaultODKCredentials: boolean;
}
interface ValidationErrors {
  organisation_id?: string;
  name?: string;
  username?: string;
  id?: string;
  short_description?: string;
  description?: string;
  hashtags?: string;
  odk_central_url?: string;
  odk_central_user?: string;
  odk_central_password?: string;
}

const regexForSymbol = /_/g;

function CreateProjectValidation(values: ProjectValues) {
  const errors: ValidationErrors = {};

  if (!values?.organisation_id) {
    errors.organisation_id = 'Organization is Required.';
  }
  if (!values?.defaultODKCredentials && !values?.odk_central_url) {
    errors.odk_central_url = 'ODK URL is Required.';
  }
  if (!values?.defaultODKCredentials && values?.odk_central_url && !isValidUrl(values.odk_central_url)) {
    errors.odk_central_url = 'Invalid URL.';
  }
  if (!values?.defaultODKCredentials && !values?.odk_central_user) {
    errors.odk_central_user = 'ODK Central User is Required.';
  }
  if (!values?.defaultODKCredentials && !values?.odk_central_password) {
    errors.odk_central_password = 'ODK Central Password is Required.';
  }
  if (!values?.name) {
    errors.name = 'Project Name is Required.';
  }
  if (values?.name && regexForSymbol.test(values.name)) {
    errors.name = 'Project Name should not contain _ .';
  }
  if (!values?.short_description) {
    errors.short_description = 'Short Description is Required.';
  }
  if (!values?.description) {
    errors.description = 'Description is Required.';
  }

  return errors;
}

export default CreateProjectValidation;
