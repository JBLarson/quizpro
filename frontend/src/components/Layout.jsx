import React from 'react';
import GlobalMenu from './GlobalMenu'; // Make sure this path is correct

const Layout = ({ children }) => {
  return (
    <>
      <GlobalMenu />
      <main className="main-page-content-wrapper"> {/* Or whatever class you use, or no class */}
        {children}
      </main>
    </>
  );
};

export default Layout;