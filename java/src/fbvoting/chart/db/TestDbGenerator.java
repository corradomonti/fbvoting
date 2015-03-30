package fbvoting.chart.db;

import it.unimi.dsi.logging.ProgressLogger;
import it.unimi.dsi.webgraph.ArrayListMutableGraph;
import it.unimi.dsi.webgraph.algo.ParallelBreadthFirstVisit;
import it.unimi.dsi.webgraph.examples.ErdosRenyiGraph;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;
import java.util.UUID;

import org.apache.commons.lang.WordUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.martiansoftware.jsap.FlaggedOption;
import com.martiansoftware.jsap.JSAP;
import com.martiansoftware.jsap.JSAPException;
import com.martiansoftware.jsap.JSAPResult;
import com.martiansoftware.jsap.Parameter;
import com.martiansoftware.jsap.SimpleJSAP;
import com.martiansoftware.jsap.Switch;
import com.martiansoftware.jsap.UnflaggedOption;
import com.mongodb.BasicDBObject;
import com.mongodb.DBCollection;
import com.mongodb.DBObject;

public class TestDbGenerator {
	
	private final static Logger LOGGER = LoggerFactory.getLogger(TestDbGenerator.class);
	
	static int N;
	static double NP;
	static int M;
	
	public static void removeDelegates(Category cat) {
		LOGGER.warn("Deleting all voting graph data for " + cat + "...");
		DBCollection dbGraph = Db.getInstance().MONGODB.getCollection("graph");
		DBObject query = new BasicDBObject("category", cat.getName());
		dbGraph.remove(query);
		LOGGER.info("Deletion of all voting graph data for " + cat + " completed.");
	}
	
	public static void fillDelegates(Category cat) {
		
		LOGGER.info("Generating random delegations for " + cat + "...");
		
		ErdosRenyiGraph erdosRenyiGraph = new ErdosRenyiGraph(N, NP/N, false);
		ParallelBreadthFirstVisit bfv = new ParallelBreadthFirstVisit(
				new ArrayListMutableGraph(erdosRenyiGraph).immutableView(),
				0, true, null);
		
		bfv.visitAll();
		
		LOGGER.info("Saving random delegations on db...");

		ProgressLogger progressLogger = new ProgressLogger(LOGGER, "arc");
		progressLogger.expectedUpdates = bfv.marker.length();
		progressLogger.start();
		
		for (int i = 0; i < bfv.marker.length(); i++) {
			storeVoteInDb(cat, i, bfv.marker.get(i));
			progressLogger.lightUpdate();
		}
		
		progressLogger.done();

		LOGGER.info("Random delegations has been generated.");
		
	}
	
	private static void storeVoteInDb(Category cat, long from, long to) {
		if (from == to)
			return;
		
		DBCollection dbGraph = Db.getInstance().MONGODB.getCollection("graph");
		DBObject item = new BasicDBObject("category", cat.getName())
							.append("from", from)
							.append("to", to);
		dbGraph.insert(item);
	}
	
	private static List<String> words;
	
	private static String randomWords() {
		if (words == null) {
			words = new ArrayList<String>();
			
			try {
				FileInputStream fis = new FileInputStream("/usr/share/dict/words");
				BufferedReader br = new BufferedReader(new InputStreamReader(fis));
				String word;
				while ((word = br.readLine()) != null) {
					word = WordUtils.capitalize(word.trim());
				    words.add(word);
				}
			} catch (IOException e) {
				throw new RuntimeException("Could not read words file.", e);
			}
		}
		
		StringBuilder title = new StringBuilder();
		do {
			title.append(words.get( (int) (Math.random() * words.size()) ));
			title.append(' ');
		} while (Math.random() > 0.5);
		
		return title.toString().trim();
	}
	
	private static String randomId() {
		return UUID.randomUUID().toString().substring(0, 8);
	}
	
	private static DBObject[] randomAdvicesSet() {
		
		LOGGER.info("Generating random set of songs...");
		
		ProgressLogger progressLogger = new ProgressLogger(LOGGER, "songs");
		progressLogger.expectedUpdates = M;
		progressLogger.start();
		
		List<DBObject> set = new ArrayList<DBObject>();
		for (int i = 0; i < M; i++) {
			DBObject item = new BasicDBObject("author", randomWords())
				.append("song", randomWords())
				.append("video", randomId());
			set.add(item);
			progressLogger.lightUpdate();
		}

		progressLogger.done();
		
		return set.toArray(new DBObject[] {});
	}
	
	public static void removeAdvices(Category cat) {
		

		LOGGER.warn("Deleting all advice data for " + cat + "...");
		DBCollection dbAdvices = Db.getInstance().MONGODB.getCollection("advices");
		DBObject query = new BasicDBObject("category", cat.getName());
		dbAdvices.remove(query);
		LOGGER.info("Deletion of all advice data for " + cat + " completed.");
			
	}
	
	private static boolean existsAdviceOf(long user, Category cat) {
		DBObject query = Db.excludingRemoved(
				new BasicDBObject("category", cat.getName())
				.append			 ("user", user)
			);
		
		DBObject result = Db.getInstance().MONGODB.getCollection("advices").findOne(query);
		
		return result != null;
	}
	
	public static void fillAdvices(Category cat) {
		
		DBObject[] advices = randomAdvicesSet();
		
		DBCollection dbGraph = Db.getInstance().MONGODB.getCollection("graph");
		DBObject query = Db.excludingRemoved(new BasicDBObject("category", cat.getName()));
		
		DBCollection dbAdvices = Db.getInstance().MONGODB.getCollection("advices");
		
		LOGGER.info("Assigning random advices for " + cat + " to each user...");
		
		ProgressLogger progressLogger = new ProgressLogger(LOGGER, "advices");
		progressLogger.start();
		
		for (DBObject item : dbGraph.find(query)) {
			for (String field : new String[] {"from", "to"}) {
				if (Math.random() < 0.9) {
					long user = (Long) item.get(field);
					if (!existsAdviceOf(user, cat)) {
						DBObject advice = advices[(int) (Math.random() * advices.length)];
						DBObject vote = new BasicDBObject("user", user)
										.append("category", cat.getName())
										.append("advice", advice);
						dbAdvices.insert(vote);
						progressLogger.lightUpdate();
					}
				}
			}
		}
		
		progressLogger.done();

		LOGGER.info("Random advices for " + cat + " has been generated.");
	}
	
	final private static Scanner INPUT = new Scanner(System.in);
	private static boolean askUserConfirmation() {
		System.out.println("Are you sure you want to delete all items? [y/n] ");
		return (INPUT.nextLine().equalsIgnoreCase("y"));
	}
	
	public static void main(String[] rawArguments) throws JSAPException {
		SimpleJSAP jsap = new SimpleJSAP(
				TestDbGenerator.class.getName(),
				"Introduce fake data in the DB.",
				new Parameter[] {
			
			new UnflaggedOption( "category", JSAP.STRING_PARSER, JSAP.REQUIRED,
					"Category for the new data (must already exists)." ),

			new Switch("graph", 'g', "graph", 
					"Insert fake graph data for the specified category"),
			new Switch("advices", 'a', "advices", 
					"Insert fake advice data for the specified category"),
			
			new Switch("deleteAll", 'D', "deleteAll", 
					"Delete every document of that category " +
					"before inserting fake data."),
					
			new FlaggedOption("N", JSAP.INTEGER_PARSER, "1000",
					JSAP.NOT_REQUIRED, 'N', "N",
					"Number of nodes in the E/R graph.") ,
					
			new FlaggedOption("NP", JSAP.DOUBLE_PARSER, "1.0",
					JSAP.NOT_REQUIRED, 'p', "NP",
					"Mean outdegree for the E/R graph.") ,
					
			new FlaggedOption("M", JSAP.INTEGER_PARSER, "100",
					JSAP.NOT_REQUIRED, 'M', "M",
					"Number of advices introduced.") ,
		});
		
		JSAPResult args = jsap.parse( rawArguments );
		if ( jsap.messagePrinted() ) System.exit( 1 );
		
		if (!(args.getBoolean("graph") | args.getBoolean("advices")))
				throw new RuntimeException("At least one between -graph and -advices should be used.");
		
		Category category = Category.find(args.getString("category"));
		
		if (args.getBoolean("graph")) {
			if (args.getBoolean("deleteAll") && askUserConfirmation() ) removeDelegates(category);
			
			TestDbGenerator.N = args.getInt("N");
			TestDbGenerator.NP = args.getDouble("NP");
			
			fillDelegates(category);
		}
		
		if (args.getBoolean("advices")){
			TestDbGenerator.M = args.getInt("M");
			if (args.getBoolean("deleteAll") && askUserConfirmation() ) removeAdvices(category);
			fillAdvices(category);
		}
	}

}
