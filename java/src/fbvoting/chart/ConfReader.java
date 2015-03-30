package fbvoting.chart;

import java.io.IOException;
import java.util.Properties;

@SuppressWarnings("serial")
public class ConfReader extends Properties {
	
	private static ConfReader instance;
	public static ConfReader getInstance() {
		if (instance == null)
			try {
				instance = new ConfReader();
			} catch (IOException e) {
				throw new RuntimeException("Could not read configurations from python.", e);
			} catch (InterruptedException e) {
				throw new RuntimeException("Python conf.py has been interrupted unexpectedly.", e);
			}
		
		return instance;
	}
	
	public final String CONF_PY_LOCATION = "../fbvoting/conf.py";

	private ConfReader() throws IOException, InterruptedException {
		Process readPythonConf = new ProcessBuilder("python", CONF_PY_LOCATION).start();
		readPythonConf.waitFor();
		load(readPythonConf.getInputStream());
		
		for (Field f : Field.values())
			if (!containsKey(f.toString()))
				throw new RuntimeException(
							"The file " + CONF_PY_LOCATION +
							" should contain property " + f + "."
						);
	}
	
	public String get(Field f) {
		return (String) get(f.toString());
	}
	
	public enum Field {
		MONGO_URI;
		
		public String value() {
			return ConfReader.getInstance().get(this);
		}
	}

}
