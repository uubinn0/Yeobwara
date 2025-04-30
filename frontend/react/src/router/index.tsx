import { Routes, Route } from "react-router-dom";
// import LoginPage from "../pages/login/page";
import HelloWorld from "../pages/HelloWorld/page";

const Router = () => {
  return (
    <Routes>
      {/* <Route path="/" element={<LoginPage />} /> */}
      <Route path="/" element={<HelloWorld />} />
    </Routes>
  );
};

export default Router;
