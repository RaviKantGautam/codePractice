import streamlit as st

def main():
    st.title("My Streamlit App")
    # Add your Streamlit code here
    st.markdown("<h1> User Registration </h1>", unsafe_allow_html=True)
    form = st.form(key='registration_form')

    def check_password(value):
        if value != form['Password']:
            form.error('Passwords do not match')
    cols1, cols2 =  form.columns(2)
    cols1.text_input(label='First Name')
    cols2.text_input(label='Last Name')
    form.text_input(label='Email')
    form.text_input(label='Username')
    pasword = form.text_input(label='Password', type='password')
    c_password = form.text_input(label='Confirm Password', type='password')
    form.text('Already have an account?')
    submit = form.form_submit_button('Submit')
    if submit:
        if pasword != c_password:
            form.error('Passwords do not match')
        else:
            st.success('Registration Successful!')


    with st.form(key='login_form'):
        cols1, cols2 = st.columns(2)
        cols1.text_input(label='Username')
        cols2.text_input(label='Password', type='password')
        st.text('Forgot Password?')
        st.form_submit_button('Login')


if __name__ == "__main__":
    main()