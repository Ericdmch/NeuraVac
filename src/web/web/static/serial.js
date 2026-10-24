function Header() {
  return React.createElement(
    'header',
    {className: 'site-header'},
    React.createElement('p', {className: 'eyebrow'}, 'NEURAVAC'),
    React.createElement('h1', null, 'Robot Control')
  );
}

function App() {
  return React.createElement(
    'main',
    {className: 'page'},
    React.createElement(Header)
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  React.createElement(App)
);
