const API = "http://127.0.0.1:8000";

let mode = "login";

const nameInput = document.getElementById("name");

nameInput.style.display = "none";

document.getElementById("loginTab").onclick = () => {

    mode = "login";

    nameInput.style.display = "none";

    document.getElementById("submitBtn").innerText = "Login";

};

document.getElementById("registerTab").onclick = () => {

    mode = "register";

    nameInput.style.display = "block";

    document.getElementById("submitBtn").innerText = "Register";

};

document.getElementById("submitBtn").onclick = async () => {

    const email = document.getElementById("email").value;

    const password = document.getElementById("password").value;

    const name = document.getElementById("name").value;

    let endpoint;
    let body;

    if(mode==="register"){

        endpoint="/register";

        body={
            name,
            email,
            password
        };

    }
    else{

        endpoint="/login";

        body={
            email,
            password
        };

    }

    const response = await fetch(API+endpoint,{

        method:"POST",

        headers:{
            "Content-Type":"application/json"
        },

        body:JSON.stringify(body)

    });

    const data=await response.json();

    if(!response.ok){

        document.getElementById("message").innerText=data.detail;

        return;

    }

    if(mode==="register"){

        alert("Registration Successful");

        return;

    }

    localStorage.setItem(
        "token",
        data.access_token
    );

    window.location="dashboard.html";

};