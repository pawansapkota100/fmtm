import React from 'react';
import '@testing-library/jest-dom';
import { Provider } from 'react-redux';
import { store } from '../../store/Store';
import { renderWithRouter } from '../../utilfunctions/testUtils';
import CreateProject from '../CreateProject';
import { screen } from '@testing-library/react';

jest.mock('axios'); // Mock axios module

describe('CreateProject Page', () => {
  it('renders create project sidebar steps', () => {
    // Render the App component in a virtual DOM environment
    const { container } = renderWithRouter(
      <Provider store={store}>
        <CreateProject />
      </Provider>,
    );

    // Check if the "EXPLORE PROJECTS" tab is rendered
    const exploreTabElement = screen.getByText('EXPLORE PROJECTS');
    expect(exploreTabElement).toBeInTheDocument();

    // Assert that the component renders without any errors
    expect(container).toBeDefined();
  });
});
