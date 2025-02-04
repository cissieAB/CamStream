
## The Receiver Side Web Application

### Application structure

```
recv-x86/                       # Current dir
│── emu_sender/
│   └── thermal_emu_app.py      # Flask thermal emu sender
│── app.py                      # Flask main application
│── templates/
│   └── index.html              # Frontend UI (Bootstrap)
│── static/
│   ├── css/
│   │   └── style.css           # Optional custom styling
│   ├── js/
│   │   └── script.js           # Optional JavaScript (if needed)
│── requirements.txt            # List of dependencies
```

- Start an emulator to send the simulated raw temperature data:
    ```bash
    python3 emu_sender/thermal_emu_app.py &  # default address is localhost:8083/raw_frame
    ```

---
### TODOS:
- Explore Flask-SocketIO instead of raw Flask as the backend for higher streaming speed.
