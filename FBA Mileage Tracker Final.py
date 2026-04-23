# REMOVE THESE THREE LINES TO STOP THE ERROR
query_params = st.query_params
default_user = query_params.get("user", "Default_User")
st.query_params["user"] = user_id_input