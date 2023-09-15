import React from 'react';
import { Link } from 'react-router-dom';
import CoreModules from '../../shared/CoreModules.js';

const boxSX = {
  'button:hover': {
    textDecoration: 'none',
  },
};
const NavigationButton = ({ link, buttonText, disabled }) => {
  return (
    <Link to={link}>
      <CoreModules.Button sx={boxSX} variant="contained" color="error" disabled={disabled}>
        {buttonText}
      </CoreModules.Button>
    </Link>
  );
};

export default NavigationButton;
