import streamlit as st
st.title("我的第一个网页工具")
st.write("这个页面是 python 画出来的,没写一行 HTML。")
name = st.text_input("你叫什么名字?")
if name:
    st.success(f"你好， {name}!")