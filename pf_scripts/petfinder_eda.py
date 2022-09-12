import pandas as pd
import sqlite3 
import pytz
import datetime
import logging
import os 
import io
import plotly.express as px 
import numpy as np 
from PIL import Image 
import sys 
sys.path.append('/home/malcolm/EmailSender/')
from EmailSender import EmailSender

tz = pytz.timezone('UTC')
pd.set_option("display.max_columns", 100)
pd.set_option("display.max_colwidth", 200)
pd.options.mode.chained_assignment = None  # default='warn'

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s')

def append_images(images, direction='horizontal',
                  bg_color=(255,255,255), aligment='center'):
    """
    Appends images in horizontal/vertical direction.
    
    https://stackoverflow.com/questions/30227466/combine-several-images-horizontally-with-python/46623632#46623632
    
    Args:
        images: List of PIL images
        direction: direction of concatenation, 'horizontal' or 'vertical'
        bg_color: Background color (default: white)
        aligment: alignment mode if images need padding;
           'left', 'right', 'top', 'bottom', or 'center'

    Returns:
        Concatenated image as a new PIL image object.
    """
    widths, heights = zip(*(i.size for i in images))

    if direction=='horizontal':
        new_width = sum(widths)
        new_height = max(heights)
    else:
        new_width = max(widths)
        new_height = sum(heights)

    new_im = Image.new('RGB', (new_width, new_height), color=bg_color)


    offset = 0
    for im in images:
        if direction=='horizontal':
            y = 0
            if aligment == 'center':
                y = int((new_height - im.size[1])/2)
            elif aligment == 'bottom':
                y = new_height - im.size[1]
            new_im.paste(im, (offset, y))
            offset += im.size[0]
        else:
            x = 0
            if aligment == 'center':
                x = int((new_width - im.size[0])/2)
            elif aligment == 'right':
                x = new_width - im.size[0]
            new_im.paste(im, (x, offset))
            offset += im.size[1]

    return new_im


def get_cnts_pcts(series):
    cnts = series.value_counts()
    pcts = 100*series.value_counts(normalize=True).round(5)
    combo = pd.concat({"Count":cnts, "Percent": pcts}, axis=1)
    return(combo)


def summarize_dog_pop(df):
    
    out = {}
    out['Count'] = df.shape[0]
    
    def parse_cnts_pcts1(df, desc):
        try:
            dict1 = {f'Top {desc} Name': df.iloc[0].name, 
                     f'Top {desc} %' : df.iloc[0]['Percent'], 
                    }
        except IndexError:
            dict1 = {f'Top {desc} Name': None, 
                     f'Top {desc} %' : None, 
                    }
        return(dict1)
    
    def parse_cnts_pcts2(df, desc):
        try:
            dict1 = {f'2nd {desc} Name': df.iloc[1].name, 
                     f'2nd {desc} %' : df.iloc[1]['Percent'], 
                }
        except IndexError:
            dict1 = {f'2nd {desc} Name': None, 
                     f'2nd {desc} %' : None, 
                }
        return(dict1)
    
    breeds = get_cnts_pcts(df['breeds.primary'])
    breeds_dict1 = parse_cnts_pcts1(breeds, 'Breed')
    breeds_dict2 = parse_cnts_pcts2(breeds, 'Breed')

    age = get_cnts_pcts(df['age'])
    age_dict1 = parse_cnts_pcts1(age, 'Age')
    age_dict2 = parse_cnts_pcts2(age, 'Age')
    
    color = get_cnts_pcts(df['colors.primary'])
    color_dict1 = parse_cnts_pcts1(color, 'Color')
    color_dict2 = parse_cnts_pcts2(color, 'Color')
    
    
    children = get_cnts_pcts(df['environment.children'])
    children_dict1 = parse_cnts_pcts1(children, 'Children')
    children_dict2 = parse_cnts_pcts2(children, 'Children')
    
    housetrained = get_cnts_pcts(df['attributes.house_trained'])
    housetrained_dict1 = parse_cnts_pcts1(housetrained, 'House Trained')
    housetrained_dict2 = parse_cnts_pcts2(housetrained, 'House Trained')
    
    dog_friendly = get_cnts_pcts(df['environment.dogs'])
    dog_friendly_dict1 = parse_cnts_pcts1(dog_friendly, 'Dog Friendly')
    dog_friendly_dict2 = parse_cnts_pcts2(dog_friendly, 'Dog Friendly')
    
    out.update(breeds_dict1)
    out.update(age_dict1)
    out.update(color_dict1)
    out.update(children_dict1)
    out.update(housetrained_dict1)
    out.update(dog_friendly_dict1)
    out.update(breeds_dict2)
    
    out_series = pd.Series(out)
    return(out_series)
    
    
def dog_days_gb_func(df, adopt_date=(datetime.datetime.now() - datetime.timedelta(days=1)).date()):
    
    df = df.sort_values('date_saved')
    
    out = {}
    out['Days ad posted'] = (df['date_saved'].max() - df['published_at'].min()).days
    adoptable_days = df[df['status'] == 'adoptable']
    out['Last Adoptable Day'] = adoptable_days['date_saved'].max()
    out['Adopted (last date)'] = df.iloc[-1]['date_saved'] >= adopt_date 
    
    out_series = pd.Series(out)
    last_record = df.iloc[0]
    out_all = pd.concat([out_series, last_record]) 
    return(out_all)


def top_org_gb_func(df):
    out = {}
    out['Count'] = df.shape[0]
    out['Unique dogs'] = df['id'].nunique()
    
    out['Avg Days in Shelter'] = df['Days bw saved and published'].mean().round(1)
    out['Lower 20% days in Shelter'] = np.quantile(df['Days bw saved and published'], 0.2)
    out['Upper 20% days in Shelter'] = np.quantile(df['Days bw saved and published'], 0.8)

    out['Added last week sum'] = df['Added in last week'].sum()
    out['Added last week pct'] = np.round(100* out['Added last week sum']/out['Count'], 2)
    
    out['Added in >4 weeks sum'] = df['Added in >4 weeks'].sum()
    out['Added in >4 weeks pct'] = np.round(100* out['Added in >4 weeks sum']/out['Count'], 2)
    
    out_series = pd.Series(out)
    return(out_series)


class PetFinderEda():
    
    def __init__(self, **kwargs):
        self.db_location = '/home/malcolm/petfinder/data/petfinder.db'
        self.today = datetime.datetime.now() - datetime.timedelta(days=1)
        self.today_str = str(datetime.datetime.now().date())
        self.two_weeks = self.today - datetime.timedelta(days=7)
        self.two_weeks_str = str(self.two_weeks.date())    
        self.debug = True
        self.image_save_folder = f'/home/malcolm/petfinder/data/result_images/{self.today_str}/'
        # Find folder with dog pics 
        folder_base = '/home/malcolm/sym_data_storage/Petfinder/Dogs/'
        folder_loc = datetime.datetime.now().strftime('%Y-%-m')
        self.dogs_pic_folder = folder_base + folder_loc +'/'
        
        
        self.metrics = {}
        self.output_dfs = {}
        self.__dict__.update(**kwargs)
        
        self.image_paths_to_send = []
        os.makedirs(self.image_save_folder, exist_ok=True)
        pass
    
    def create_con(self):
        self.con = sqlite3.connect(self.db_location)
        self.cursor = self.con.cursor()
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        logger.info(self.cursor.fetchall())
        
    def get_new_old_existing_dogs(self):

        sql2 = f"""

        with two_weeks_dogs as (
        select id as id_old
        , status as status_old
        , status_changed_at as status_change_old
        , date_saved as date_saved_old
        from dog_10475_30mi
        where date_saved = '{self.two_weeks_str}'
        ) , 
        today_dogs as (
        select id as id_new
        , status as status_new
        , status_changed_at as status_change_new
        , date_saved as date_saved_new
        from dog_10475_30mi
        where date_saved = '{self.today_str}'
        )


        select count(*)
        , count(distinct id_new) as `Dogs in Shelter Now`
        , count(distinct id_old) as `Dogs in Shelter Last Week`
        , sum(case when id_old is null then 1 else 0 end) as `Dogs Entered Shelter` -- Old doesn't have key so dog must be new
        , sum(case when id_new is null then 1 else 0 end) as `Dogs Left Shelter` -- New doesn't have key so dog must be old 
        , sum(case when id_old is not null and id_new is not null then 1 else 0 end) as `Dogs Remained in Shelter`
        , min(date_saved_old) as start_date
        , max(date_saved_new) as end_date

        from (
        SELECT id_new, status_new, status_change_new, date_saved_new
        , id_old, status_old, status_change_old, date_saved_old
        from two_weeks_dogs
        left join today_dogs
        on two_weeks_dogs.id_old = today_dogs.id_new

        UNION 

        SELECT id_new, status_new, status_change_new, date_saved_new
        , id_old, status_old, status_change_old, date_saved_old
        from today_dogs 
        left join two_weeks_dogs
        on today_dogs.id_new = two_weeks_dogs.id_old
        )x

        """

        self.new_old_existing = pd.read_sql(sql2, self.con)
        self.output_dfs['New Old Existing'] = self.new_old_existing
        
    def load_raw_data(self):
        self.data_raw = pd.read_sql(f"""
        select dogs.*, orgs.name as org_name 
        from dog_10475_30mi dogs
        left join Organizations orgs
        on dogs.organization_id = orgs.id
        where date_saved between '{self.two_weeks_str}' and '{self.today_str}'
        """ , self.con)
        self.data_raw['published_at'] = pd.to_datetime(self.data_raw['published_at'])
        self.data_raw['status_changed_at'] = pd.to_datetime(self.data_raw['status_changed_at'])
        
        self.data_raw['date_saved'] = pd.to_datetime(self.data_raw['date_saved'], utc=True)
        self.latest_day_df = self.data_raw[self.data_raw['date_saved'] == self.data_raw['date_saved'].max()]
        
        logger.info("Number of datapoints in data_raw: " + str(self.data_raw.shape[0]))
        logger.info("Number of data points in latest day: " + str(self.latest_day_df.shape[0]))
        
    def get_top_orgs(self):
        org_value_counts = get_cnts_pcts(self.latest_day_df['org_name'])
        self.top_n_dog_orgs = org_value_counts.sort_values('Count', ascending=False).iloc[:4].index.tolist()
        logger.info("Top n dog orgs: " + str(self.top_n_dog_orgs))
        self.output_dfs['Top Orgs'] = org_value_counts.iloc[:4]
             
    def get_dog_days_gb(self):
        self.dog_gb = self.data_raw.groupby('id').apply(dog_days_gb_func)
        self.adopted_df = self.dog_gb[self.dog_gb['Adopted (last date)'] == False]
        logger.info("Dog days in shelter df shape: " + str(self.dog_gb.shape))
        # Analysis 
        long_ad_posted_dogs = self.dog_gb[self.dog_gb['Days ad posted'] >= 180]
        long_ad_posted_age_cnts = get_cnts_pcts(long_ad_posted_dogs['age'])\
            .rename({'Count': '6 Mo+ Ad Count', 
                    'Percent': '6 Mo+ Ad Pct'}, axis=1 )
        age_cnts = get_cnts_pcts(self.dog_gb['age'])\
            .rename({'Count': 'Full Pop Count',
                      'Percent': 'Full Pop Pct'}, axis= 1)
        long_ad_posted_age_cnts = pd.merge(long_ad_posted_age_cnts, age_cnts, left_index=True, right_index=True)
        long_ad_posted_age_cnts['Sample Ratio'] = (long_ad_posted_age_cnts['6 Mo+ Ad Pct']/age_cnts['Full Pop Pct']).round(2)
        self.long_ad_posted_age_cnts = long_ad_posted_age_cnts
        self.output_dfs['Long Ad Posted DF'] = self.long_ad_posted_age_cnts
        
    def summarize_latest_day(self):
        all_summaries = {}
        all_summaries['Latest Day'] = summarize_dog_pop(self.latest_day_df)
        all_summaries['Adopted'] = summarize_dog_pop(self.adopted_df)
        for org in self.top_n_dog_orgs:
            all_summaries[org] = summarize_dog_pop(self.latest_day_df[self.latest_day_df['org_name'] == org])
        self.all_summaries_df = pd.concat(all_summaries, axis=1)
        self.output_dfs['All Summaries'] = self.all_summaries_df

    def create_top_orgs_over_time_dfs(self):
        top_orgs = self.output_dfs['Top Orgs'].index.tolist()
        ns_raw = self.data_raw[self.data_raw['org_name'].isin(top_orgs)]
        ns_raw['Days bw saved and published'] = (ns_raw['date_saved'] - ns_raw['published_at']).dt.days
        ns_raw['Added in last week'] = ns_raw['Days bw saved and published'] <= 7
        ns_raw['Added in >4 weeks']  = ns_raw['Days bw saved and published'] >= 28
        self.top_orgs_raw = ns_raw
        self.top_orgs_gb_df = self.top_orgs_raw.groupby(['date_saved', 'org_name']).apply(top_org_gb_func)
        logger.debug("Finished Top Orgs over Time")
        
    def create_top_org_plots(self):
        # Shuffle the dataframe  
        cols = ['Avg Days in Shelter', 'Upper 20% days in Shelter']
        days_in_regroup = pd.concat({x : self.top_orgs_gb_df[x] for x in cols})\
            .reset_index()\
            .rename({'level_0':'Days Measure', 
                    0 : "# of Days"}, axis=1)
        
        # Create ands save first plot 
        n_days_per_org_img = px.line(days_in_regroup, 'date_saved', '# of Days'
            , color='org_name'
            , line_dash='Days Measure'
            , title='Number of Days (average, top decile) in Shelter over Time'                         
            )
        n_days_per_org_img_pil = Image.open(io.BytesIO(n_days_per_org_img.to_image()))
        
        # Create and save second plot 
        n_dogs_in_shelter_img = px.line(self.top_orgs_gb_df.reset_index(), 'date_saved', 'Unique dogs'
           , color = 'org_name'
           , title= 'Number of Dogs in Shelter')
        n_dogs_in_shelter_img_pil = Image.open(io.BytesIO(n_dogs_in_shelter_img.to_image()))
        
        # Create and save third plot 
        last_week_dogs_img = px.line(self.top_orgs_gb_df.reset_index(), 'date_saved', 'Added last week pct'
           , color = 'org_name'
           , title= 'Number of Dogs in Shelter <7 days'
           )
        last_week_dogs_img_pil = Image.open(io.BytesIO(last_week_dogs_img.to_image()))

    
        # Create and save third plot 
        dogs_still_there_img = px.line(self.top_orgs_gb_df.reset_index(), 'date_saved', 'Added in >4 weeks pct'
           , color = 'org_name'
           , title= 'Number of Dogs in Shelter >4 weeks'
           )
        dogs_still_there_img_pil = Image.open(io.BytesIO(dogs_still_there_img.to_image()))
        
        top_row = append_images([last_week_dogs_img_pil, dogs_still_there_img_pil]
                                 , direction='horizontal') 
        bottom_row = append_images([n_days_per_org_img_pil, n_dogs_in_shelter_img_pil]
                                , direction='horizontal')
        full_pic = append_images([top_row, bottom_row], direction='vertical')
        pic_loc = self.image_save_folder + 'Charts.png'
        full_pic.save(pic_loc)
        self.image_paths_to_send.append(pic_loc)
        
        logger.debug('Finished Creating Images')
        
    def get_pics_to_send(self):
       
        # Get dogs pics I can send 
        img_pics_df = pd.read_sql(f"""
            select max(dogs.name) as dog_name
            , max(`breeds.primary`) as breed, max(gender) as gender, max(size) as size
            , max(`colors.primary`) as color
            , max(orgs.name) as org_name, max(`contact.address.city`) as city, min(img.date_saved) as img_date_saved
            , max(description) as description--, max(tags) tags
            , max(Image_Status) img_loc, dogs.id
            from dog_10475_30mi dogs
            left join Organizations orgs
            on dogs.organization_id = orgs.id
            left join Dog_Image_Status img
            on dogs.id = img.id
            where img.date_saved between '{self.two_weeks_str}' and '{self.today_str}'
            and img.Image_Status is not null 
            and img.Image_Status != ''
            group by dogs.id
            order by dogs.id 
            """ , self.con)
        logger.debug("Dog Img Shape: ", img_pics_df.shape)
        selected_pics = img_pics_df[img_pics_df['img_loc'] != 'could not save image'].sample(n=4, random_state=123)
        pic_locs = selected_pics['img_loc'].tolist()
        self.output_dfs['Dogs in Imgs'] = selected_pics.drop(['img_loc'], axis=1)

        # Create One image with 4 dog pics 
        dog_imgs = [Image.open(x) for x in pic_locs]
        dog_img1 = append_images([dog_imgs[0], dog_imgs[1]]
                                , direction='horizontal')
        dog_img2 = append_images([dog_imgs[2], dog_imgs[3]]
                                , direction='horizontal')
        dog_img3 =  append_images([dog_img1, dog_img2], direction='vertical')
        img_path = self.image_save_folder + f'random_dogs_{self.today_str}.jpeg'
        dog_img3.save(img_path)
        self.image_paths_to_send.append(img_path)
        
    def cleanup(self):
        self.con.commit()
        self.con.close()
        logger.debug('Finished Cleanup ')
        
    def execute(self):
        self.create_con()
        self.get_new_old_existing_dogs()
        self.load_raw_data()
        self.get_top_orgs()
        self.get_dog_days_gb()
        self.summarize_latest_day()
        self.create_top_orgs_over_time_dfs()
        self.create_top_org_plots()
        self.get_pics_to_send()
        self.cleanup()
        

if __name__ == '__main__':
    pf_eda = PetFinderEda()
    pf_eda.execute()
    
    html_dict = {k:v.to_html() for k, v in pf_eda.output_dfs.items() }
    body_html = f"""
    This email contains a report of the <b>dogs</b> listed on Petfinder.com from {pf_eda.two_weeks_str} to {pf_eda.today_str} 
    for all locations 30 miles from 10475. 

    It contains summary information about the Number of dogs in shelters as of {pf_eda.today_str}, top organizations
    , dogs who have been in shelters the longest. 
    <br>
    <br>
    <b>Adoptions</b>
    {html_dict['New Old Existing']}
    <br>
    <br>
    <b>Time in Shelter </b>
    {html_dict['Long Ad Posted DF']}
    <br>
    <br>
    <b>Shelters with Most Dogs </b> 
    {html_dict['Top Orgs']}
    <br>
    <br>
    <b>Summary of Dogs in Shelter </b>
    {html_dict['All Summaries']}
    <br>
    <br>
    <b>Dogs in Image</b> 
    {html_dict['Dogs in Imgs']}
    """

    email_sender = EmailSender(**message_params)
    email_sender.execute()
