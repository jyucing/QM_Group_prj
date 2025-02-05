import pandas as pd
import util


class AllDataFrameInOne:
    def __init__(self, rentDataFile: str, crimeDataFile: str):
        self._rent_df_ = util.format_read_csv(rentDataFile)
        self._borough_crime_df_ = util.format_read_csv(crimeDataFile)
        # The df used for linear regression
        self.reg_df_ = None

    def filter_crime_minor(self, tar_col: str):
        return self._borough_crime_df_[self._borough_crime_df_['MinorText'] == tar_col]

    def join_tables(self, crime_type: str, crime_year: int, rent_year: str):
        """
        @TODO: Comments on the way...
        :param crime_type: The specific type of crime in 'MinorText' column
        :param crime_year: The first year sum from
        :param rent_year: In type of '20XX-XX'
        :return: A left joint dataset contains borough name, crime data sum in a year and rent year
        """
        filtered_crime_df = self.filter_crime_minor(crime_type)
        columns = [str(year_month) for year_month in range(crime_year, crime_year + 12)]
        filtered_crime_df['year_total'] = filtered_crime_df[columns].sum(axis=1)
        filtered_crime_df = filtered_crime_df.iloc[:, :3].join(filtered_crime_df['year_total'])

        joined_data = pd.merge(filtered_crime_df, self._rent_df_,
                               left_on='LookUp_BoroughName',
                               right_on='Area', how='left')

        # Handle the NA data and remove them
        joined_data.replace('..', pd.NA, inplace=True)
        joined_data.dropna(inplace=True)
        self.reg_df_ = joined_data[['Area', 'year_total', rent_year]]
        return self.reg_df_

    def join_multi_row(self, selected_crime: list, crime_year: int, rent_year: str):
        """
        @TODO: Comments on the way...
        :param selected_crime: It should be a list saves more than one crime type
                                Like the 'selected_crimes' in main
        :param crime_year: Used to sum a years all cases
        :param rent_year: The data in this year
        :return: merged dataframe used for multi linear regression
        """
        filtered_crime_data = self._borough_crime_df_[self._borough_crime_df_['MinorText'].isin(selected_crime)]

        if filtered_crime_data is None:
            raise Exception("Fail to find target crime type")

        # Columns for the year 2020
        columns = [str(year_month) for year_month in range(crime_year, crime_year + 12)]
        # Group by borough and sum the monthly data for the 'rent_year'
        filtered_crime_data = filtered_crime_data.groupby(['LookUp_BoroughName', 'MinorText'])[columns].sum()
        filtered_crime_data['year_total'] = filtered_crime_data.sum(axis=1)
        # Pivot the crime data count
        filtered_crime_data = filtered_crime_data.reset_index().pivot(index='LookUp_BoroughName',
                                                                      columns='MinorText',
                                                                      values='year_total')

        rent_data = self._rent_df_[['Area', rent_year]].dropna()
        rent_data[rent_year] = pd.to_numeric(rent_data[rent_year], errors='coerce')

        merged_data = pd.merge(filtered_crime_data, rent_data,
                               left_index=True,
                               right_on='Area')

        self.reg_df_ = merged_data
        return self.reg_df_

    def print_column_names(self):
        print(self._rent_df_.columns)
        print("____")
        print(self._borough_crime_df_.columns)

