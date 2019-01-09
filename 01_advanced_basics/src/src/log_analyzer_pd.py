# Log analyzer script using pandas
import pandas as pd
import os, logging, sys, re, argparse, json

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}
names = ['remote_addr', 'remote_user', 'empty_1', 'http_x_real_ip', 'time_local', 'timezone', 'request', 'status', 'body_bytes_sent',
         'http_referer', "http_user_agent", "http_x_forwarded_for", "http_X_REQUEST_ID", "http_X_RB_USER", 'request_time']
res_names = ['url', 'count', 'count_perc', 'time_sum', 'time_perc', 'time_avg', 'time_max', 'time_med']

def get_log_file_name(log_dir=config['LOG_DIR']):
    log_files = {re.findall('nginx-access-ui.log-([^\.]+)', f)[0]: f for f in os.listdir('.'+log_dir) if re.match(r'nginx-access-ui.log-', f)}
    return log_files[max(log_files, key=int)]

def parse_command_line_arguments(config):
    parser = argparse.ArgumentParser()
    parser.add_argument(
            '--config', type=argparse.FileType('r'),
            help='Configuration json file'
            )
    args = parser.parse_args()
    defaults = config
    if args.config:
        try:
            defaults = json.load(args.config)
        except ValueError:
            print('Error: Could not parse config file', sys.stderr.write())
        finally:
            args.config.close()
    return defaults

def read_log_name(config):
    actual_log_file_name, actual_date = get_log_file_name(), re.findall('log-([^\.]+)', get_log_file_name())[0]
    report_file = '.' + config['REPORT_DIR'] + '/report-' + actual_date[:4] + '.' + actual_date[4:6] + '.' + actual_date[6:] + '.html'
    print('Last actual log date is ' + actual_date + ', loading...')
    return actual_log_file_name, actual_date, report_file

def load_log(actual_log_file_name, names, config):
    return pd.read_table('.' + config['LOG_DIR'] + '/' + actual_log_file_name, sep=' ', names=names, index_col=False)

def process_log(actual_log_file_name, actual_date, report_file, df, res_names):
    print('Processing report for ' + actual_date + '...')
    url_regexp = '([^\s]+)\sHTTP'
    df['url'] = df['request'].str.extract(url_regexp, expand=False)
    res = df.groupby(['url']).agg({'request_time':['count', 'sum', 'mean', 'max', 'median']}).reset_index()
    res.columns = res.columns.droplevel(0)
    res['time_perc'], res['count_perc'] = 100 * res['sum'] / res['sum'].sum(), 100 * res['count'] / res['count'].sum()
    res.columns = ['url', 'count', 'time_sum', 'time_avg', 'time_max', 'time_med', 'time_perc', 'count_perc']
    return res[res_names].sort_values('time_sum', ascending=False).reset_index(drop=True)

def write_report(res, report_file, actual_date):
    path = os.path.dirname(report_file)
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError:
            print ("Creation of the directory %s failed" % path)
        else:
            print ("Successfully created the directory %s " % path)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_colwidth',100)
    pd.set_option('display.float_format', lambda x: '%.3f' % x)
    res.to_html(report_file, index=False)
    print('Report done for ' + actual_date)

def main():
    # Reading config
    actual_config = parse_command_line_arguments(config)

    # Reading log
    actual_log_file_name, actual_date, report_file = read_log_name(config=actual_config)

    # Check_if_report_exists
    if os.path.isfile(report_file):
        print('!!! Last actual date report file already exists !!!')
        sys.exit()

    # Loading log file
    df = load_log(actual_log_file_name, names, config=actual_config)

    # Processing log
    res = process_log(actual_log_file_name, actual_date, report_file, df, res_names)

    # Writing html report
    write_report(res, report_file, actual_date)

# main
if __name__ == "__main__":
    main()
