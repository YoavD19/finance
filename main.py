#imports
from sqlalchemy.exc import IntegrityError, DataError
import pandas as pd
import streamlit as st
import plotly.express as px
import time
from pages_utils import goto_page, goto_page_if_logged_in
from db_utils import read_query_df, run_query, return_run_query, cache_read_query, hash_password, check_password, cache_general_data

st.set_page_config(
    page_title="StackSight",       # Title shown in the browser tab
    page_icon="💸",                # Icon shown in the browser tab
    )

# Initialize session state for page navigation
if "page" not in st.session_state:
    st.session_state.page = "Home"

if "username" not in st.session_state: #initialize username
    st.session_state.username = "Guest"

#home page
if st.session_state.page == "Home": 
    st.title("Home🏠")
    col1, col2, col3= st.columns(3)
    col1.markdown("### Hello "+ st.session_state.username + "!")
    col2.button("Login", on_click= goto_page, args=("Login",),type="primary", use_container_width=True)
    col3.button("Sign Up", on_click= goto_page, args=("Signup",),type="primary", use_container_width=True)

    st.divider()

    colA, colB, colC = st.columns(3)
    colA.button(":green[Charts]", on_click= goto_page_if_logged_in, args=("Charts",), use_container_width=True)
    colB.button(":blue[Tables]", on_click= goto_page_if_logged_in, args=("Tables",), use_container_width=True)
    colC.button(":orange[Insert]", on_click= goto_page_if_logged_in, args=("Insert",), use_container_width=True)

#Login page  
elif st.session_state.page == "Login":
    users = return_run_query(query_str="SELECT uname,pword FROM users")
    user_pass_dict = {user[0]: user[1] for user in users}
    st.title("Login")
    with st.form("Login Form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        if submit_button:
            if username in user_pass_dict and check_password(password, user_pass_dict[username]):
                st.success(f"Welcome {username}!")
                st.session_state.username = username
                time.sleep(1)
                goto_page("Home")
                st.rerun()
            else:
                st.error("Invalid username or password.")
    st.write("Don't have an account?")
    st.button("Sign Up", on_click= goto_page, args=("Signup",))
    st.write("Already logged in?")
    st.button("Home", on_click= goto_page, args=("Home",))
    
#signup page
elif st.session_state.page == "Signup":
    st.title("Signup")
    with st.form("Signup Form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        email = st.text_input("Email")
        submit_button = st.form_submit_button("Sign Up")
        if submit_button:
            if username == '' or password == '' or email == '':
                st.error("Please fill in all fields.")
            else:
                try:
                    run_query(query_str="INSERT INTO users (uname, pword, email) VALUES (:username, :password, :email)",
                              params={"username": username, "password": hash_password(password), "email": email}
                              )
                    st.session_state.username = username
                    st.success(f"Account created for {username}!")
                    time.sleep(1)
                    goto_page("Home")
                    st.rerun()
                except IntegrityError:
                    st.error("Username already exists. Please choose a different username.")
                except DataError:
                    st.error("Invalid data format. Please check your input.")

    st.write("Already have an account?")
    st.button("Login", on_click= goto_page, args=("Login",))
    st.write("Already logged in?")
    st.button("Home", on_click= goto_page, args=("Home",))

#Charts page
elif st.session_state.page == "Charts":
    st.title("Charts")
    if st.button("↩ Home"):
        st.session_state.selected_accounts = []
        st.session_state.chart = None
        goto_page("Home")
        st.rerun()
    st.divider()

    if "chart" not in st.session_state:  # Initialize chart state
        st.session_state.chart = None

    if "selected_filters" not in st.session_state:  # Initialize selected filters state
        st.session_state.selected_filters = []

    if "filter" not in st.session_state:  # Initialize filter state
        st.session_state.filter = "account_num"

    left, right = st.columns(2)

    filter_dict = cache_general_data({"Account Number": "account_num",
                   "Company": "company_t",
                   "Company Type": "ctype_t",
                   "Financial Plan": "plan_t",
                   "Financial Path": "fin_path_t"})
    
    

    if left.button("Separated", use_container_width=True):
        st.session_state.chart = "Separated"
        st.session_state.selected_filters = []  # Update selected accounts state

    if right.button("Combined", use_container_width=True):
        st.session_state.chart = "Combined"
        st.session_state.selected_filters = []  # Update selected accounts state

    if st.session_state.chart == "Separated":
        st.subheader("Separated")
        st.session_state.filter = st.pills("Filter By", options=list(filter_dict.keys()), default="Account Number")
        filter_list = return_run_query(query_str=f"""SELECT DISTINCT {filter_dict[st.session_state.filter]} FROM accounts
                                    INNER JOIN companies ON accounts.company = companies.company
                                    INNER JOIN financial_plans ON accounts.plan = financial_plans.plan
                                    INNER JOIN paths ON accounts.fin_path = paths.fin_path
                                    INNER JOIN company_types ON companies.ctype = company_types.ctype
                                   WHERE uname = :username""",
                                       params={"username": st.session_state.username})
        filter_options = [account[0] for account in filter_list]
        st.session_state.selected_filters = st.multiselect(f"Select {st.session_state.filter}", filter_options, default=filter_options)
        df= read_query_df(f"""WITH cte AS (SELECT accounts.uname, updates.account_num, updates.money, updates.begda,
                accounts.company, companies.company_t,
                accounts.plan, financial_plans.plan_t,
                accounts.fin_path, paths.fin_path_t,
                companies.ctype, company_types.ctype_t
                FROM updates
                INNER JOIN accounts ON updates.account_num = accounts.account_num
                INNER JOIN companies ON accounts.company = companies.company
                INNER JOIN financial_plans ON accounts.plan = financial_plans.plan
                INNER JOIN paths ON accounts.fin_path = paths.fin_path
                INNER JOIN company_types ON companies.ctype = company_types.ctype
                where accounts.uname = :username
                )
                SELECT {filter_dict[st.session_state.filter]} as "{st.session_state.filter}",
                        sum(money) as "Amount Of Money",
                        begda as "Date"
                        FROM cte
                        WHERE {filter_dict[st.session_state.filter]} in :filter_list
                        GROUP BY {filter_dict[st.session_state.filter]}, begda
                        ORDER BY begda
                """, params={"username": st.session_state.username, "filter_list": st.session_state.selected_filters}
               )

    if st.session_state.chart == "Combined":
        st.subheader("Combined")
        st.session_state.filter = st.pills("Filter By", options=list(filter_dict.keys()), default="Account Number")
        filter_list = return_run_query(query_str=f"""SELECT DISTINCT {filter_dict[st.session_state.filter]} FROM accounts
                                    INNER JOIN companies ON accounts.company = companies.company
                                    INNER JOIN financial_plans ON accounts.plan = financial_plans.plan
                                    INNER JOIN paths ON accounts.fin_path = paths.fin_path
                                    INNER JOIN company_types ON companies.ctype = company_types.ctype
                                   WHERE uname = :username""",
                                       params={"username": st.session_state.username})
        filter_options = [account[0] for account in filter_list]
        st.session_state.selected_filters = st.multiselect(f"Select {st.session_state.filter}", filter_options, default=filter_options)
        df=read_query_df(query_str=f"""WITH cte AS (SELECT accounts.uname, updates.account_num, updates.money, updates.begda,
                                        accounts.company, companies.company_t,
                                        accounts.plan, financial_plans.plan_t,
                                        accounts.fin_path, paths.fin_path_t,
                                        companies.ctype, company_types.ctype_t
                                        FROM updates
                                        INNER JOIN accounts ON updates.account_num = accounts.account_num
                                        INNER JOIN companies ON accounts.company = companies.company
                                        INNER JOIN financial_plans ON accounts.plan = financial_plans.plan
                                        INNER JOIN paths ON accounts.fin_path = paths.fin_path
                                        INNER JOIN company_types ON companies.ctype = company_types.ctype
                                        where accounts.uname = :username
                                        )
                                    SELECT sum(money) as "Amount Of Money",
                                    begda as "Date"
                                    FROM cte
                                    WHERE {filter_dict[st.session_state.filter]} IN :filter_list
                                    GROUP BY begda
                                    ORDER BY begda""",
                               params={"username": st.session_state.username, "filter_list": st.session_state.selected_filters})


    try:
        fig = px.line(df, x="Date", y="Amount Of Money", color=st.session_state.filter if st.session_state.chart == "Separated" else None)
        fig.update_xaxes(tickformat="%b %Y", dtick="M1")
        st.plotly_chart(fig, use_container_width=True)
    except NameError:
        st.info("Please select a chart to display data.")
#Tables page
elif st.session_state.page == "Tables":
    st.title("Tables")
    if st.button("↩ Home"):
        st.session_state.selected_accounts = []
        st.session_state.table = None
        goto_page("Home")
        st.rerun()
    st.divider()

    if "table" not in st.session_state:  # Initialize table state
        st.session_state.table = None

    if "selected_accounts" not in st.session_state:  # Initialize selected accounts state
        st.session_state.selected_accounts = []

    left, right = st.columns(2)

    accounts_list = return_run_query(query_str="SELECT account_num FROM accounts WHERE uname = :username",
            params={"username": st.session_state.username})
    account_options = [account[0] for account in accounts_list]

    
    if left.button("Latest Data", use_container_width=True):
        st.session_state.table = "Latest Data"

    if right.button("All Data", use_container_width=True):
        st.session_state.table = "All Data"

    if st.session_state.table == "Latest Data":
        st.subheader("Latest Data")
        st.session_state.selected_accounts = st.multiselect("Select Accounts", account_options, default=account_options)
        # Execute the query with the selected accounts
        df = read_query_df(query_str="""SELECT account_num "Account Number",
                                company_t "Company",
                                ctype_t "Company Type",
                                plan_t "Plan",
                                fin_path_t "Path",
                                money "Amount Of Money",
                                begda "Last Updated"
                                FROM (
                                    SELECT accounts.uname,
                                    accounts.account_num,
                                    companies.company_t,
                                    company_types.ctype_t,
                                    financial_plans.plan_t,
                                    paths.fin_path_t,
                                    updates.money,
                                    updates.begda,
                                    row_number() OVER (partition by accounts.account_num ORDER by updates.begda DESC) as R
                                    from accounts
                                    INNER join users on accounts.uname = users.uname
                                    INNER join companies on accounts.company = companies.company
                                    INNER join company_types on companies.ctype = company_types.ctype
                                    INNER join financial_plans on accounts.plan = financial_plans.plan
                                    INNER join paths on accounts.fin_path = paths.fin_path
                                    INNER join updates on accounts.account_num = updates.account_num
                                )
                                WHERE R = 1
                                AND uname = :username
                                AND account_num in :accounts""",
                                params={"username": st.session_state.username, "accounts": st.session_state.selected_accounts})
    if st.session_state.table == "All Data":
        st.subheader("All Data")
        st.session_state.selected_accounts = st.multiselect("Select Accounts", account_options, default=account_options)
        df = read_query_df(query_str=""" SELECT accounts.account_num "Account Number",
                                    companies.company_t "Company",
                                    company_types.ctype_t "Company Type",
                                    financial_plans.plan_t "Plan",
                                    paths.fin_path_t "Path",
                                    updates.money "Amount Of Money",
                                    updates.begda "Last Updated"
                                    FROM accounts
                                    INNER join users on accounts.uname = users.uname
                                    INNER join companies on accounts.company = companies.company
                                    INNER join company_types on companies.ctype = company_types.ctype
                                    INNER join financial_plans on accounts.plan = financial_plans.plan
                                    INNER join paths on accounts.fin_path = paths.fin_path
                                    INNER join updates on accounts.account_num = updates.account_num
                                    WHERE accounts.uname = :username
                                    AND accounts.account_num in :accounts
                                    ORDER BY accounts.account_num, updates.begda DESC""",
                                      params={"username": st.session_state.username, "accounts": st.session_state.selected_accounts})

    # temporary query
    try:
        st.dataframe(df, hide_index=True, use_container_width=True, column_config={"Last Updated": st.column_config.DateColumn("Date", format="MMM YYYY")})
    except NameError:
        st.info("Please select a table to display data.")


#Insert page
elif st.session_state.page == "Insert":
    st.title("Insert")
    if st.button("↩ Home"):
        st.session_state.form = None
        goto_page("Home")
        st.rerun()
    st.divider()
    if "form" not in st.session_state:  # Initialize form state
        st.session_state.form = None
    left, right = st.columns(2)
    
    if left.button("Add account", use_container_width=True):
        st.session_state.form = "Add Account Form"
    if right.button("Update account", use_container_width=True):
        st.session_state.form = "Update Account Form"
    if st.session_state.form == "Add Account Form":
        with st.form("Add Account Form"):
            account_num = st.text_input("Account Number")
            companies = cache_read_query(query_str="SELECT company_t FROM companies")
            plans = cache_read_query(query_str="SELECT plan_t FROM financial_plans")
            paths = cache_read_query(query_str="SELECT fin_path_t FROM paths")
            company = st.selectbox("Company", [company[0] for company in companies])
            plan = st.selectbox("Financial Plan", [plan[0] for plan in plans])
            fin_path = st.selectbox("Financial Path", [path[0] for path in paths])
            submit_button = st.form_submit_button("Add")
            if submit_button:
                if account_num == '':
                    st.error("Please enter an account number.")
                else:
                    try:
                        run_query(query_str="""INSERT INTO accounts (uname, company, account_num, plan, fin_path)
                                        SELECT
                                        :username AS uname,
                                        (SELECT company FROM companies WHERE company_t = :company),
                                        :account_num AS account_num,
                                        (SELECT plan FROM financial_plans WHERE plan_t = :plan),
                                        (SELECT fin_path FROM paths WHERE fin_path_t = :fin_path)""",
                           params={"username": st.session_state.username, "company": company, "account_num": account_num, "plan": plan, "fin_path": fin_path}
                        )
                        st.success(f"Account {account_num} added successfully!")
                        time.sleep(1)
                        st.session_state.form = None  # Reset form state
                        st.rerun()

                    except IntegrityError:
                        st.error("Account number already exists. Please choose a different account number.")
                    except DataError:
                        st.error("Invalid data format. Please check your input.")


    # update account form
    elif st.session_state.form == "Update Account Form":
        with st.container(border=True):
            # Fetch accounts for the current user
            accounts = return_run_query(query_str="SELECT account_num FROM accounts WHERE uname = :username",
                                          params={"username": st.session_state.username})
            account_num = st.selectbox("Select Account", [account[0] for account in accounts])
            account_info = return_run_query(query_str="""SELECT company_t, plan_t, fin_path_t, company_link
                                    FROM accounts
                                    INNER JOIN companies ON accounts.company = companies.company
                                    INNER JOIN financial_plans ON accounts.plan = financial_plans.plan
                                    INNER JOIN paths ON accounts.fin_path = paths.fin_path
                                    WHERE account_num = :account_num""",
                                          params={"account_num": account_num})
            st.link_button(f"{account_info[0][0]} | {account_info[0][1]} | {account_info[0][2]}🔗", account_info[0][3])
            money = st.number_input("Money", step=1000.00, min_value=0.00, max_value=99999999.99)
            year = st.number_input("Year", step=1, min_value=2000, max_value=pd.Timestamp.now().year, value=pd.Timestamp.now().year)
            month = st.number_input("Month", step=1, min_value=1, max_value=12, value=pd.Timestamp.now().month)
            begda = pd.Timestamp(year=year, month=month, day=1)
            submit_button = st.button("Update")
            if submit_button:
                if account_num == '':
                    st.error("Please select an account.")
                else:
                    try:
                        run_query(query_str="""INSERT INTO updates (account_num, money, begda)
                                    VALUES (:account_num, :money, :begda)
                                  ON CONFLICT (account_num, begda) DO UPDATE
                                    SET money = EXCLUDED.money""",
                                params={"account_num": account_num, "money": money, "begda": begda}
                            )
                        st.success(f"Account {account_num} updated successfully!")
                        time.sleep(1)
                        st.session_state.form = None  # Reset form state
                        st.rerun()
                    except DataError:
                        st.error("Invalid data format. Please check your input.")

