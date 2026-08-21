import {
  SearchIcon,
  GridIcon,
  BellIcon,
  BookmarkIcon,
  HeartIcon,
  PencilIcon,
  UserCircleIcon,
} from './icons'

function NavIconLink({ icon, label, badge }) {
  return (
    <a className="navbar-icon-link" href="#" onClick={(e) => e.preventDefault()}>
      <span className="navbar-icon-wrap">
        {icon}
        {badge && <span className="navbar-badge">{badge}</span>}
      </span>
      <span>{label}</span>
    </a>
  )
}

function NavBar() {
  return (
    <header className="navbar">
      <a className="navbar-logo" href="#" onClick={(e) => e.preventDefault()}>
        <img src="/metrade.jpeg" alt="MeTrade Jobs" />
      </a>

      <div className="navbar-search">
        <SearchIcon />
        <input type="text" placeholder="Search all of MeTrade" readOnly />
      </div>

      <nav className="navbar-links">
        <NavIconLink icon={<GridIcon />} label="Categories" />
        <NavIconLink icon={<BellIcon />} label="Notifications" badge={17} />
        <NavIconLink icon={<BookmarkIcon />} label="Watchlist" />
        <NavIconLink icon={<HeartIcon />} label="Favourites" />
        <a className="navbar-cta" href="#" onClick={(e) => e.preventDefault()}>
          <PencilIcon />
          <span>Start a listing</span>
        </a>
        <a className="navbar-profile" href="#" onClick={(e) => e.preventDefault()}>
          <UserCircleIcon />
          <span>My MeTrade</span>
        </a>
      </nav>
    </header>
  )
}

export default NavBar
