import React, { useEffect, useState } from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { MyOrganisationDataService, OrganisationDataService } from '@/api/OrganisationService';
import { user_roles } from '@/types/enums';
import { GetOrganisationDataModel } from '@/models/organisation/organisationModel';
import OrganisationGridCard from '@/components/organisation/OrganisationGridCard';
import OrganisationCardSkeleton from '@/components/organisation/OrganizationCardSkeleton';
import windowDimention from '@/hooks/WindowDimension';
import { useAppSelector } from '@/types/reduxTypes';

const Organisation = () => {
  const dispatch = CoreModules.useAppDispatch();
  //dispatch function to perform redux state mutation

  const { type } = windowDimention();
  //get window dimension

  const [searchKeyword, setSearchKeyword] = useState<string>('');
  const [activeTab, setActiveTab] = useState<0 | 1>(0);
  const [verifiedTab, setVerifiedTab] = useState<boolean>(true);
  const [myOrgsLoaded, setMyOrgsLoaded] = useState(false);
  const token = CoreModules.useAppSelector((state) => state.login.loginToken);
  const defaultTheme = useAppSelector((state) => state.theme.hotTheme);

  const organisationData = useAppSelector((state) => state.organisation.organisationData);
  const myOrganisationData = useAppSelector((state) => state.organisation.myOrganisationData);

  const organisationDataLoading = useAppSelector((state) => state.organisation.organisationDataLoading);
  const myOrganisationDataLoading = useAppSelector((state) => state.organisation.myOrganisationDataLoading);
  // loading states for the organisations from selector

  let cardsPerRow = new Array(
    type == 'xl' ? 3 : type == 'lg' ? 3 : type == 'md' ? 3 : type == 'sm' ? 2 : type == 's' ? 2 : 1,
  ).fill(0);
  // calculate number of cards to display according to the screen size

  const handleSearchChange = (event) => {
    setSearchKeyword(event.target.value);
  };
  const filteredBySearch = (data: GetOrganisationDataModel[], searchKeyword: string) => {
    const filteredCardData: GetOrganisationDataModel[] = data?.filter((d) =>
      d.name.toLowerCase().includes(searchKeyword.toLowerCase()),
    );
    return filteredCardData;
  };

  useEffect(() => {
    if (verifiedTab) {
      dispatch(OrganisationDataService(`${import.meta.env.VITE_API_URL}/organisation/`));
    } else {
      dispatch(OrganisationDataService(`${import.meta.env.VITE_API_URL}/organisation/unapproved/`));
    }
  }, [verifiedTab]);

  const loadMyOrganisations = () => {
    if (!myOrgsLoaded) {
      dispatch(MyOrganisationDataService(`${import.meta.env.VITE_API_URL}/organisation/my-organisations`));
      setMyOrgsLoaded(true);
    }
    setActiveTab(1);
  };

  return (
    <CoreModules.Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        background: '#f0efef',
        flex: 1,
        gap: 2,
      }}
      className="fmtm-p-5"
    >
      <div className="md:fmtm-hidden fmtm-border-b-white fmtm-border-b-[1px]">
        <div className="fmtm-flex fmtm-justify-between fmtm-items-center">
          <h1 className="fmtm-text-xl sm:fmtm-text-2xl fmtm-mb-1 sm:fmtm-mb-2">MANAGE ORGANIZATIONS</h1>
        </div>
      </div>
      <div className="fmtm-flex fmtm-flex-col md:fmtm-flex-row md:fmtm-justify-between md:fmtm-items-center fmtm-gap-2">
        <CoreModules.Box>
          <CoreModules.Tabs sx={{ minHeight: 'fit-content' }}>
            <CoreModules.Tab
              label="All"
              sx={{
                background: activeTab === 0 ? 'grey' : 'white',
                color: activeTab === 0 ? 'white' : 'grey',
                minWidth: 'fit-content',
                width: 'auto',
                '&:hover': { backgroundColor: '#999797', color: 'white' },
                fontSize: ['14px', '16px', '16px'],
                minHeight: ['26px', '36px', '36px'],
                height: ['30px', '36px', '36px'],
                px: ['12px', '16px', '16px'],
              }}
              className="fmtm-duration-150"
              onClick={() => setActiveTab(0)}
            />
            <CoreModules.Tab
              label="My Organizations"
              sx={{
                background: activeTab === 1 ? 'grey' : 'white',
                color: activeTab === 1 ? 'white' : 'grey',
                marginLeft: ['8px', '12px', '12px'],
                minWidth: 'fit-content',
                width: 'auto',
                '&:hover': { backgroundColor: '#999797', color: 'white' },
                fontSize: ['14px', '16px', '16px'],
                minHeight: ['26px', '36px', '36px'],
                height: ['30px', '36px', '36px'],
                px: ['12px', '16px', '16px'],
              }}
              className="fmtm-duration-150"
              onClick={() => loadMyOrganisations()}
            />
            {token && (
              <CoreModules.Link to={'/create-organization'}>
                <CoreModules.Button
                  variant="outlined"
                  color="error"
                  startIcon={<AssetModules.AddIcon />}
                  sx={{
                    marginLeft: ['8px', '12px', '12px'],
                    minWidth: 'fit-content',
                    width: 'auto',
                    fontWeight: 'bold',
                    minHeight: ['26px', '36px', '36px'],
                    height: ['30px', '36px', '36px'],
                    px: ['12px', '16px', '16px'],
                  }}
                >
                  New
                </CoreModules.Button>
              </CoreModules.Link>
            )}
          </CoreModules.Tabs>
        </CoreModules.Box>
        {token !== null && token['role'] && token['role'] === user_roles.ADMIN && activeTab === 0 && (
          <CoreModules.Box>
            <CoreModules.Tabs sx={{ minHeight: 'fit-content' }}>
              <CoreModules.Tab
                label="To be Verified"
                sx={{
                  background: !verifiedTab ? 'grey' : 'white',
                  color: !verifiedTab ? 'white' : 'grey',
                  minWidth: 'fit-content',
                  width: 'auto',
                  '&:hover': { backgroundColor: '#999797', color: 'white' },
                  fontSize: ['14px', '16px', '16px'],
                  minHeight: ['26px', '36px', '36px'],
                  height: ['30px', '36px', '36px'],
                  px: ['12px', '16px', '16px'],
                }}
                className="fmtm-duration-150"
                onClick={() => setVerifiedTab(false)}
              />
              <CoreModules.Tab
                label="Verified"
                sx={{
                  background: verifiedTab ? 'grey' : 'white',
                  color: verifiedTab ? 'white' : 'grey',
                  marginLeft: ['8px', '12px', '12px'],
                  minWidth: 'fit-content',
                  width: 'auto',
                  '&:hover': { backgroundColor: '#999797', color: 'white' },
                  fontSize: ['14px', '16px', '16px'],
                  minHeight: ['26px', '36px', '36px'],
                  height: ['30px', '36px', '36px'],
                  px: ['12px', '16px', '16px'],
                }}
                className="fmtm-duration-150"
                onClick={() => setVerifiedTab(true)}
              />
            </CoreModules.Tabs>
          </CoreModules.Box>
        )}
      </div>
      <CoreModules.Box>
        <CoreModules.TextField
          variant="outlined"
          size="small"
          placeholder="Search organization"
          value={searchKeyword}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <CoreModules.InputAdornment position="start">
                <AssetModules.SearchIcon />
              </CoreModules.InputAdornment>
            ),
          }}
          className="fmtm-min-w-[14rem] lg:fmtm-w-[20%]"
        />
      </CoreModules.Box>
      {activeTab === 0 ? (
        !organisationDataLoading ? (
          <CoreModules.Stack
            sx={{
              display: {
                xs: 'flex',
                sm: 'flex',
                md: 'flex',
                lg: 'flex',
                xl: 'flex',
                flexDirection: 'row',
                justifyContent: 'left',
                width: '100%',
                gap: 10,
              },
            }}
          >
            <OrganisationCardSkeleton defaultTheme={defaultTheme} cardsPerRow={cardsPerRow} />
          </CoreModules.Stack>
        ) : (
          <OrganisationGridCard
            filteredData={filteredBySearch(organisationData, searchKeyword)}
            allDataLength={organisationData?.length}
          />
        )
      ) : null}
      {activeTab === 1 ? (
        !myOrganisationDataLoading ? (
          <CoreModules.Stack
            sx={{
              display: {
                xs: 'flex',
                sm: 'flex',
                md: 'flex',
                lg: 'flex',
                xl: 'flex',
                flexDirection: 'row',
                justifyContent: 'left',
                width: '100%',
                gap: 10,
              },
            }}
          >
            <OrganisationCardSkeleton defaultTheme={defaultTheme} cardsPerRow={cardsPerRow} />
          </CoreModules.Stack>
        ) : (
          <OrganisationGridCard
            filteredData={filteredBySearch(myOrganisationData, searchKeyword)}
            allDataLength={myOrganisationData?.length}
          />
        )
      ) : null}
    </CoreModules.Box>
  );
};

export default Organisation;
