package fbvoting.chart;

import it.unimi.dsi.logging.ProgressLogger;
import it.unimi.dsi.webgraph.BVGraph;
import it.unimi.dsi.webgraph.ImmutableGraph;

import java.io.File;
import java.io.IOException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import fbvoting.chart.db.Category;
import fbvoting.chart.db.Delegates;
import fbvoting.util.ScatteredArcsGraph;

public class Voting {

	
	private final static Logger LOGGER = LoggerFactory.getLogger(Voting.class);
	
	private ScatteredArcsGraph fbIdGraph;
	private ImmutableGraph graph;

	public Voting(Category cat) throws IOException {
		File tmpFile = File.createTempFile("fbvoting-" + cat.getName(), "-tmp");
		String graphPath = tmpFile.getAbsolutePath();
		
		LOGGER.info("Importing voting graph from MongoDB...");
		fbIdGraph = new ScatteredArcsGraph(
				Delegates.getVotes(cat),
				false, // symmetrize,
				false, //noLoops,
				1024 /* ?????? */, //batchSize, 
				tmpFile.getParentFile(),
				new ProgressLogger()
		);
		
		BVGraph.store(fbIdGraph, graphPath);
		
		LOGGER.info("Loading voting graph from BVGraph file...");
		graph = ImmutableGraph.load(graphPath);
	}
	
	public long[] ids() {
		return fbIdGraph.ids;
	}
	
	public ImmutableGraph graph() {
		return graph;
	}

}
