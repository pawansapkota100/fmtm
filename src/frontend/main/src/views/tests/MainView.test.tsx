import React from 'react';
import { screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import MainView from '../MainView';
import { store } from '../../store/Store';
import { renderWithRouter } from '../../utilfunctions/testUtils';
import { Provider } from 'react-redux';

describe('Main Page', () => {
  test('renders the app bar with correct elements', () => {
    renderWithRouter(
      <Provider store={store}>
        <MainView />
      </Provider>,
    );

    // Check if the "EXPLORE PROJECTS" tab is rendered
    const exploreTabElement = screen.getByText('EXPLORE PROJECTS');
    expect(exploreTabElement).toBeInTheDocument();

    // Check if the "MANAGE ORGANIZATIONS" tab is rendered
    const manageOrgTabElement = screen.getByText('MANAGE ORGANIZATIONS');
    expect(manageOrgTabElement).toBeInTheDocument();
  });
});
