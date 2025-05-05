import { Routes, Route } from "react-router-dom";
import HelloWorld from "../pages/HelloWorld/page";
// import HomePage from "../pages/home/page";
import LoginPage from "../pages/login/page";
import SignupPage from "../pages/signup/page";
// import ChatPage from "../pages/chat/page";

const Router = () => {
  return (
    <Routes>
      <Route path="/helloworld" element={<HelloWorld />} />
      {/* <Route path="/" element={<HomePage />} /> */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      {/* <Route path="/chat" element={<ChatPage />} /> */}
    </Routes>
  );
};

export default Router;
